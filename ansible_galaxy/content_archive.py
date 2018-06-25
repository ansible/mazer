import fnmatch
import logging
import os
import tarfile

from ansible_galaxy import exceptions
from ansible_galaxy.models import content
from ansible_galaxy.models import content_archive

log = logging.getLogger(__name__)

# TODO: better place to define?
META_MAIN = os.path.join('meta', 'main.yml')
GALAXY_FILE = 'ansible-galaxy.yml'
APB_YAML = 'apb.yml'


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


# TODO/FIXME: try to make sense of this and find_archive_parent_dir
def find_archive_metadata(archive_members):
    '''Try to find the paths to the archives meta data files

    Aka, meta/main.yml or ansible-galaxy.yml.

    Also, while we are at it, try to find the archive parent
    dir.'''

    meta_file = None
    galaxy_file = None

    meta_parent_dir = None
    archive_parent_dir = None

    apb_yaml_file = None

    for member in archive_members:
        if fnmatch.fnmatch(member.name, '*/%s' % APB_YAML):
            log.debug('apb.yml member: %s', member)
            apb_yaml_file = member.name

        if META_MAIN in member.name or GALAXY_FILE in member.name:
            # Look for parent of meta/main.yml
            # Due to possibility of sub roles each containing meta/main.yml
            # look for shortest length parent
            meta_parent_dir = os.path.dirname(os.path.dirname(member.name))
            if not meta_file:
                archive_parent_dir = meta_parent_dir
                if GALAXY_FILE in member.name:
                    galaxy_file = member
                else:
                    meta_file = member
            else:
                # self.log.debug('meta_parent_dir: %s archive_parent_dir: %s len(m): %s len(a): %s member.name: %s',
                #               meta_parent_dir, archive_parent_dir,
                #               len(meta_parent_dir),
                #               len(archive_parent_dir),
                #               member.name)
                if len(meta_parent_dir) < len(archive_parent_dir):
                    archive_parent_dir = meta_parent_dir
                    meta_file = member
                    if GALAXY_FILE in member.name:
                        galaxy_file = member
                    else:
                        meta_file = member

    log.debug('apb_yaml_file: %s', apb_yaml_file)
    # FIXME: return a real type/object for archive metadata
    return (meta_file,
            meta_parent_dir,
            galaxy_file,
            apb_yaml_file)


def find_archive_parent_dir(archive_members, content_type, content_dir):
    # archive_parent_dir wasn't found when checking for metadata files
    archive_parent_dir = None

    shortest_dir = None
    for member in archive_members:
        # This is either a new-type Galaxy Content that doesn't have an
        # ansible-galaxy.yml file and the type desired is specified and
        # we check parent dir based on the correct subdir existing or
        # we need to just scan the subdirs heuristically and figure out
        # what to do
        member_dir = os.path.dirname(os.path.dirname(member.name))
        shortest_dir = shortest_dir or member_dir

        if len(member_dir) < len(shortest_dir):
            shortest_dir = member_dir

        if content_type != "all":
            if content_dir and content_dir in member.name:
                archive_parent_dir = os.path.dirname(member.name)
                return archive_parent_dir
        else:
            for plugin_dir in content.CONTENT_TYPE_DIR_MAP.values():
                if plugin_dir in member.name:
                    archive_parent_dir = os.path.dirname(member.name)
                    return archive_parent_dir

    if content_type not in content.CONTENT_TYPES:
        log.debug('did not find a content_dir or plugin_dir, so using shortest_dir %s for archive_parent_dir', shortest_dir)
        return shortest_dir

    # TODO: archive format exception?
    msg = "No content metadata provided, nor content directories found for content_type: %s" % \
        content_type
    log.debug('content_type: %s', content_type)
    log.debug('content_dir: %s', content_dir)
    raise exceptions.GalaxyClientError(msg)


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
    (meta_file, meta_parent_dir, dummy, apb_yaml_file) = \
        find_archive_metadata(members)

    archive_type = detect_content_archive_type(archive_path, members)
    log.debug('archive_type: %s', archive_type)

    # log.debug('self.content_type: %s', self.content_type)
    # if not archive_parent_dir:
    #    archive_parent_dir = archive.find_archive_parent_dir(members,
    #                                                         content_type=content_meta.content_type,
    #                                                         content_dir=content_meta.content_dir)

    log.debug('meta_file: %s', meta_file)
    log.debug('archive_type: %s', archive_type)
    log.debug("archive_parent_dir: %s", archive_parent_dir)
    log.debug("meta_parent_dir: %s", meta_parent_dir)

    # metadata_ = archive.load_archive_role_metadata(content_tar_file,
    #                                               meta_file)

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
