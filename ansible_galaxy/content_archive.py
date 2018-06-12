import logging
import os
import tarfile

from ansible_galaxy import archive
from ansible_galaxy import exceptions
from ansible_galaxy.models import content
from ansible_galaxy.models import content_archive

log = logging.getLogger(__name__)


def detect_content_archive_type(archive_path, archive_members):
    '''Try to determine if we are a role, multi-content, apb etc.

    if there is a meta/main.yml ->  role

    if there is any of the content types subdirs -> multi-content'''

    # FIXME: just looking for the root dir...

    top_dir = archive_members[0].name

    log.debug('top_dir: %s', top_dir)

    meta_main_target = os.path.join(top_dir, 'meta/main.yml')

    type_dirs = content.CONTENT_TYPE_DIR_MAP.values()
    log.debug('type_dirs: %s', type_dirs)

    type_dir_targets = set([os.path.join(top_dir, x) for x in type_dirs])
    log.debug('type_dir_targets: %s', type_dir_targets)

    for member in archive_members:
        if member.name == meta_main_target:
            return 'role'
        if member.name in type_dir_targets:
            return 'multi-content'

    # TODO: exception
    return None


def load_archive(archive_path):
    archive_parent_dir = None

    if not tarfile.is_tarfile(archive_path):
        raise exceptions.GalaxyClientError("the file downloaded was not a tar.gz")

    if archive_path.endswith('.gz'):
        content_tar_file = tarfile.open(archive_path, "r:gz")
    else:
        content_tar_file = tarfile.open(archive_path, "r")

    members = content_tar_file.getmembers()

    archive_parent_dir = members[0].name

    # next find the metadata file
    (meta_file, meta_parent_dir, galaxy_file, apb_yaml_file) = \
        archive.find_archive_metadata(members)

    archive_type = detect_content_archive_type(archive_path, members)
    log.debug('archive_type: %s', archive_type)

    # log.debug('self.content_type: %s', self.content_type)
    # if not archive_parent_dir:
    #    archive_parent_dir = archive.find_archive_parent_dir(members,
    #                                                         content_type=content_meta.content_type,
    #                                                         content_dir=content_meta.content_dir)

    log.debug('meta_file: %s', meta_file)
    log.debug('galaxy_file: %s', galaxy_file)
    log.debug('archive_type: %s', archive_type)
    log.debug("archive_parent_dir: %s", archive_parent_dir)
    log.debug("meta_parent_dir: %s", meta_parent_dir)

    # if not meta_file and not galaxy_file and self.content_type == "role":
    #    raise exceptions.GalaxyClientError("this role does not appear to have a meta/main.yml file or ansible-galaxy.yml.")

    # metadata_ = archive.load_archive_role_metadata(content_tar_file,
    #                                               meta_file)

    # galaxy_metadata = archive.load_archive_galaxyfile(content_tar_file,
    #                                                  galaxy_file)

    # apb_data = archive.load_archive_apb_yaml(content_tar_file,
    #                                          apb_yaml_file)

    # log.debug('apb_data: %s', pprint.pformat(apb_data))

    # looks like we are a role, update the default content_type from all -> role
    if archive_type == 'role':
        # Look for top level role metadata
        # archive_role_metadata = \
        #    archive.load_archive_role_metadata(content_tar_file,
        #                                       os.path.join(archive_parent_dir, archive.META_MAIN))
        log.debug('Find role metadata in the archive, so installing it as role content_type')

        archive_meta = content_archive.RoleContentArchiveMeta(top_dir=archive_parent_dir)
        # content_meta = content.RoleContentArchiveMeta.from_data(data)

        log.debug('role archive_meta: %s', archive_meta)

        return content_tar_file, archive_meta

    return content_tar_file, content_archive.ContentArchiveMeta(archive_type=archive_type,
                                                                top_dir=archive_parent_dir)

# TODO: add back galaxy, apb meta data load
#    if apb_data:
#        log.debug('Find APB metadata in the archive, so installing it as APB content_type')
#
#        data = self.content_meta.data
#        data['apb_data'] = apb_data
#
#        content_meta = content.APBContentArchiveMeta.from_data(data)
#
#        log.debug('APB content_meta: %s', content_meta)
#        content_archive_type = 'apb'
#
#    log.debug('content_archive_type=%s', content_archive_type)
