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

    for member in archive_members:
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

    archive_type = detect_content_archive_type(archive_path, members)
    log.debug('archive_type: %s', archive_type)

    # log.debug('self.content_type: %s', self.content_type)
    # if not archive_parent_dir:
    #    archive_parent_dir = archive.find_archive_parent_dir(members,
    #                                                         content_type=content_meta.content_type,
    #                                                         content_dir=content_meta.content_dir)

    log.debug('archive_type: %s', archive_type)
    log.debug("archive_parent_dir: %s", archive_parent_dir)

    # looks like we are a role, update the default content_type from all -> role
    if archive_type == 'role':
        # Look for top level role metadata
        # archive_role_metadata = \
        #    archive.load_archive_role_metadata(content_tar_file,
        #                                       os.path.join(archive_parent_dir, archive.META_MAIN))
        log.debug('Found role metadata in the archive, so installing it as role content_type')

    archive_meta = content_archive.ContentArchiveMeta(top_dir=archive_parent_dir,
                                                      archive_type=archive_type,
                                                      archive_path=archive_path)

    log.debug('role archive_meta: %s', archive_meta)

    return content_tar_file, archive_meta
