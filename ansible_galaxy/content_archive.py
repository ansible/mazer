import datetime
import logging
import os
import tarfile

import attr

from ansible_galaxy import archive
from ansible_galaxy import exceptions
from ansible_galaxy import install_info
from ansible_galaxy.models import content
from ansible_galaxy.models.content_archive import ContentArchiveInfo
from ansible_galaxy.models.install_info import InstallInfo

log = logging.getLogger(__name__)

# TODO: better place to define?
META_MAIN = os.path.join('meta', 'main.yml')
GALAXY_FILE = 'ansible-galaxy.yml'
APB_YAML = 'apb.yml'


def null_display_callback(*args, **kwargs):
    log.debug('display_callback: %s', args)


@attr.s()
class ContentArchive(object):
    info = attr.ib(type=ContentArchiveInfo)
    tar_file = attr.ib(type=tarfile.TarFile, default=None)
    install_datetime = attr.ib(type=datetime.datetime,
                               default=None)

    display_callback = attr.ib(default=null_display_callback)
    META_INSTALL = os.path.join('meta', '.galaxy_install_info')

    def extract(self):
        '''do the file extraction bits'''
        pass

    def install_info(self, content_namespace, content_name, content_version, install_datetime, extract_to_path):
        namespaced_content_path = '%s/%s' % (content_namespace,
                                             content_name)

        info_path = os.path.join(extract_to_path,
                                 namespaced_content_path,
                                 self.META_INSTALL)

        content_install_info = InstallInfo.from_version_date(version=content_version,
                                                             install_datetime=install_datetime)

        # TODO: this save will need to be moved to a step later. after validating install?
        install_info.save(content_install_info, info_path)

    def install(self, content_namespace, content_name, content_version, extract_to_path, force_overwrite=False):
        all_installed_files, install_datetime = \
            self.extract(content_namespace, content_name,
                         extract_to_path, force_overwrite=force_overwrite)

        install_info = self.install_info(content_namespace, content_name, content_version,
                                         install_datetime=install_datetime,
                                         extract_to_path=extract_to_path)
        return install_info


@attr.s()
class TraditionalRoleContentArchive(ContentArchive):

    def extract(self, content_namespace, content_name, extract_to_path,
                display_callback=None, force_overwrite=False):

        # TODO: move to content info validate step in install states?
        if not content_namespace:
            # TODO: better error
            raise exceptions.GalaxyError('While installing a role , no namespace was found. Try providing one with --namespace')

        label = "%s.%s" % (content_namespace, content_name)
        # log.debug('content_meta: %s', content_meta)

        log.info('About to extract "%s" to %s', label, extract_to_path)

        tar_members = self.tar_file.members
        parent_dir = tar_members[0].name

        namespaced_content_path = '%s/%s/%s/%s' % (content_namespace,
                                                   content_name,
                                                   'roles',
                                                   content_name)

        log.debug('namespaced role path: %s', namespaced_content_path)

        all_installed_paths = []
        files_to_extract = []
        for member in tar_members:
            # rel_path ~  roles/some-role/meta/main.yml for ex
            rel_path = member.name[len(parent_dir) + 1:]

            namespaced_role_rel_path = os.path.join(content_namespace, content_name, 'roles',
                                                    content_name, rel_path)
            files_to_extract.append({
                'archive_member': member,
                'dest_dir': extract_to_path,
                'dest_filename': namespaced_role_rel_path,
                'force_overwrite': force_overwrite})

        file_extractor = archive.extract_files(self.tar_file, files_to_extract)

        installed_paths = [x for x in file_extractor]
        install_datetime = datetime.datetime.utcnow()

        all_installed_paths.extend(installed_paths)

        # TODO: InstallResults object? installedPaths, InstallInfo, etc?
        return all_installed_paths, install_datetime


@attr.s()
class CollectionContentArchive(ContentArchive):
    display_callback = attr.ib(default=null_display_callback)
    META_INSTALL = os.path.join('meta', '.galaxy_install_info')

    def extract(self, content_namespace, content_name, extract_to_path,
                display_callback=None, force_overwrite=False):
        self.display_callback('- extracting all content from "%s"' % (content_name))
        all_installed_paths = []
        files_to_extract = []
        tar_members = self.tar_file.getmembers()
        parent_dir = tar_members[0].name

        for member in tar_members:
            rel_path = member.name[len(parent_dir) + 1:]
            namespaced_role_rel_path = os.path.join(content_namespace, content_name, rel_path)
            files_to_extract.append({
                'archive_member': member,
                'dest_dir': extract_to_path,
                'dest_filename': namespaced_role_rel_path,
                'force_overwrite': force_overwrite})

        file_extractor = archive.extract_files(self.tar_file, files_to_extract)

        install_datetime = datetime.datetime.utcnow()

        installed_paths = [x for x in file_extractor]
        all_installed_paths.extend(installed_paths)

        # TODO: InstallResults object? installedPaths, InstallInfo, etc?
        return all_installed_paths, install_datetime




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
    log.debug("archive_parent_dir: %s", archive_parent_dir)

    # looks like we are a role, update the default content_type from all -> role
    if archive_type == 'role':
        log.debug('Found role metadata in the archive, so installing it as role content_type')

    archive_info = ContentArchiveInfo(top_dir=archive_parent_dir,
                                      archive_type=archive_type,
                                      archive_path=archive_path)

    log.debug('role archive_info: %s', archive_info)

    # factory-ish
    if archive_type in ['multi-content']:
        content_archive_ = CollectionContentArchive(info=archive_info,
                                                    tar_file=content_tar_file)
    elif archive_type in ['role']:
        content_archive_ = TraditionalRoleContentArchive(info=archive_info,
                                                         tar_file=content_tar_file)
    else:
        content_archive_ = ContentArchive(info=archive_info,
                                          tar_file=content_tar_file)

    log.debug('content archive_: %s', content_archive_)

    return content_archive_
    # return content_tar_file, archive_info
