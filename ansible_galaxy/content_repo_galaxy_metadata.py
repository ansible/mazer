
# view/control/serializer/helper/utils/interface/misc
# for the galaxy metadata found in a ansible-galaxy.yml
# in a content repo


import logging

from ansible_galaxy import archive
from ansible_galaxy import exceptions
from ansible_galaxy.models import content
from ansible_galaxy.utils.yaml_parse import yaml_parse
from ansible_galaxy.display import null_display_callback

_sample = '''
---
meta_version: '0.1'  # metadata format version
modules:
 - path: playbooks/modules/*
 - path: modules/galaxyfile_sample_module.py
   dependencies:
    - src: module_utils/*
 - path: modules/module_c.py
   dependencies:
    - src: git+https://github.com/maxamillion/test-galaxy-content
      type: module_utils
'''

log = logging.getLogger(__name__)

# FIXME: terrible temp interface just to get the code out of content.py


def install_from_galaxy_metadata(content_tar_file,
                                 archive_parent_dir,
                                 galaxy_metadata,
                                 content_meta,
                                 display_callback=None,
                                 force_overwrite=False):

    installed = []
    content_sections = []

    display_callback = display_callback or null_display_callback

    # find the sections that define how content will be installed
    for galaxy_metadata_section in galaxy_metadata:
        log.debug('galaxy_metadata_section=%s', galaxy_metadata_section)

        if galaxy_metadata_section in ('meta_version', 'repo_name', 'namespace'):
            log.debug('nothing to do for galaxy_metadata_section=%s', galaxy_metadata_section)
            continue
        content_sections.append(galaxy_metadata_section)

    # just the content sections
    for content_section in content_sections:
        log.debug('content_section=%s', content_section)

        # TODO: should be default behavior of content type specific ContentMeta subclasses
        # default behaviors for the type of content references by this section
        _content_dir = content.CONTENT_TYPE_DIR_MAP.get(content_section, None)
        _content_type = content_section

        if content_section == 'modules':
            _content_dir = 'library'
            _content_type = 'module'

        log.debug('content_section=%s, _contend_dir=%s, _content_type=%s',
                  content_section, _content_dir, _content_type)

        # TODO/FIXME: really need ContentType classes for the defaults for each content type
        #             ie, ModuleContentType, CallbackPluginsContentType, etc
        #
        # FIXME: this is creating a ContentMeta for the general content type we are dealing with
        _content_meta = content.GalaxyContentMeta(name=content_meta.name,
                                                  src=content_meta.src,
                                                  version=content_meta.version,
                                                  scm=content_meta.scm,
                                                  path=content_meta.path,
                                                  content_type=_content_type,
                                                  content_dir=_content_dir,
                                                  requires_meta_main=False)

        res = install_by_galaxy_metadata(content_tar_file,
                                         archive_parent_dir,
                                         _content_meta,
                                         galaxy_metadata,
                                         content_section,
                                         display_callback=display_callback,
                                         force_overwrite=force_overwrite)
        log.debug('res=%s', res)
        installed.extend(res)

    return installed


def install_by_galaxy_metadata(content_tar_file,
                               archive_parent_dir,
                               content_meta,
                               galaxy_metadata,
                               galaxy_metadata_section,
                               display_callback=None,
                               force_overwrite=False):
    '''based on galaxy metadata file, install stuff, eventually include deps

    and return a list of the stuff installed (a list of tuples of (content_meta, install_result)).'''
    installed = []

    display_callback = display_callback or null_display_callback

    # FIXME: suppose this is basically options for setting up a deserializer
    # FIXME: def should be elsewhere, likely some serializer class
    for content_stanza in galaxy_metadata[galaxy_metadata_section]:
        log.debug('content_stanza=%s', content_stanza)

        path_pattern = content_stanza['path']

        log.debug('galaxy md modules content=%s', content_stanza)
        log.debug('galaxy md modules path_pattern=%s', path_pattern)

        # FIXME: os.sep seems wrong here, the yaml format shouldn't care?
        member_matches = archive.filter_members_by_fnmatch(content_tar_file, '*/%s' % path_pattern)

        import pprint
        log.debug('member_matches=%s', pprint.pformat(member_matches))

        log.info('about to extract content_type=%s %s to %s',
                 content_meta.content_type, content_meta.name, content_meta.path)

        res = archive.extract_by_content_type(content_tar_file,
                                              archive_parent_dir,
                                              content_meta,
                                              files_to_extract=member_matches,
                                              # content_type=content_meta.content_type,
                                              extract_to_path=content_meta.path,
                                              force_overwrite=force_overwrite)
        log.debug('res: %s', res)

        installed.append((content_meta, res))

        break

        # FIXME: on a general level, having content that only sometimes has dep info seems like a problem
        if 'dependencies' not in content_stanza:
            continue

        installed_deps = install_deps_by_galaxy_metadata(content_deps=content_stanza['dependencies'],
                                                         parent_content_meta=content_meta,
                                                         display_callback=display_callback)
        installed.extend(installed_deps)

    return installed


def install_deps_by_galaxy_metadata(content_deps,
                                    parent_content_meta,
                                    display_callback=None):

    installed = []
    for content_dep in content_deps:
        if 'src' not in content_dep:
            raise exceptions.GalaxyClientError("ansible-galaxy.yml dependencies must provide a src")

        res = install_dep_by_galaxy_metadata(content_dep,
                                             parent_content_meta=parent_content_meta,
                                             display_callback=display_callback)

        installed.extend(res)

    return installed


def install_dep_by_galaxy_metadata(content_dep,
                                   parent_content_meta,
                                   display_callback=None):

    display_callback = display_callback or null_display_callback

    # FIXME - Should we assume this to be true for module deps?
    # FIXME: ContentSpec object?
    # TODO: classmethod for GalaxyContentMeta.from_galaxy_metadata_dep()
    content_meta = content.GalaxyContentMeta(src=yaml_parse(content_dep['src']),
                                             content_type=content_dep.get('type', None),
                                             scm=content_dep.get('scm', None),
                                             path=parent_content_meta.path,
                                             version=content_dep.get('version', None),
                                             # needs map
                                             content_dir=content_dep.get('type', None))

    display_callback('- processing dependency (skipping FIXME): %s' % content_meta.src)

    # This is an external dep, treat it as such
    if content_meta.scm:
        log.debug('need to install a content dep %s from remote, but skipping FIXME', content_meta)
        # TODO: add a GalaxyContent.from_content_metadata() classmethod constructor
#        dep_content = GalaxyContent(self.galaxy, **content_meta.data)
#        try:
#            installed = dep_content.install()
#        except exceptions.GalaxyClientError as e:
#            display_callback("- dependency %s was NOT installed successfully: %s " %
#                             (dep_content.name, str(e)), level='warning')
#        return
    else:
        # the dep is also in the content repo the galaxy_metadata is from, so just
        # extract it (or better, add it to the accumulated list of things to extract)
        log.debug('looks like the dep %s is a dep from the same repo, skipping for now FIXME',
                  content_meta)

    return [(content_meta, [])]
