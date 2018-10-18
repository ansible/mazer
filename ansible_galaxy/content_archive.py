import datetime
import logging
import os
import tarfile

import attr

from ansible_galaxy import archive
from ansible_galaxy import exceptions
from ansible_galaxy import install_info
from ansible_galaxy import role_metadata
from ansible_galaxy.models import content
from ansible_galaxy.models.content_archive import ContentArchiveInfo
from ansible_galaxy.models.install_info import InstallInfo
from ansible_galaxy.models.installation_results import InstallationResults

log = logging.getLogger(__name__)

# TODO: better place to define?
META_MAIN = os.path.join('meta', 'main.yml')
GALAXY_FILE = 'ansible-galaxy.yml'
APB_YAML = 'apb.yml'


def null_display_callback(*args, **kwargs):
    log.debug('display_callback: %s', args)


@attr.s()
class BaseContentArchive(object):
    info = attr.ib(type=ContentArchiveInfo)
    tar_file = attr.ib(type=tarfile.TarFile, default=None)
    install_datetime = attr.ib(type=datetime.datetime,
                               default=None)

    display_callback = attr.ib(default=null_display_callback)
    META_INSTALL = os.path.join('meta', '.galaxy_install_info')

    def __attrs_post_init__(self):
        self.log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))

    def content_dest_root_subpath(self, content_namespace, content_name):
        '''The relative path inside the installed content where extract should consider the root

        A collection archive for 'my_namespace.my_content' will typically be extracted to
        '~/.ansible/content/my_namespace/my_content' in which case the content_dest_root_subpath
        should return just '/'.

        But Role archives will be extracted into a 'roles' sub dir of the typical path.
        ie, a 'my_namespace.my_role' role archive will need to be extracted to
        '~/.ansible/content/my_namespace/roles/my_role/' in which case the content_dest_root_subpatch
        should return 'roles/my_roles' (ie, 'roles/%s' % content_name)
        '''
        return ''

    def extract(self, content_namespace, content_name, extract_to_path,
                display_callback=None, force_overwrite=False):

        all_installed_paths = []

        # TODO: move to content info validate step in install states?
        if not content_namespace:
            # TODO: better error
            raise exceptions.GalaxyError('While installing a role , no namespace was found. Try providing one with --namespace')

        label = "%s.%s" % (content_namespace, content_name)

        # 'extract_to_path' is for ex, ~/.ansible/content
        self.log.info('About to extract %s "%s" to %s', self.info.archive_type, label, extract_to_path)
        self.display_callback('- extracting %s content from "%s"' % (self.info.archive_type, label))

        tar_members = self.tar_file.members

        # This assumes the first entry in the tar archive / tar members
        # is the top dir of the content, ie 'my_content_name-branch' for collection
        # or 'ansible-role-my_content-1.2.3' for a traditional role.
        parent_dir = tar_members[0].name

        content_dest_root_subpath = self.content_dest_root_subpath(content_namespace, content_name)
        # self.log.debug('content_dest_root_subpath: %s', content_dest_root_subpath)

        content_dest_root_path = os.path.join(content_namespace,
                                              content_name,
                                              content_dest_root_subpath)

        # self.log.debug('content_dest_root_path1: |%s|', content_dest_root_path)

        # TODO: need to support deleting all content in the dirs we are targetting
        #       first (and/or delete the top dir) so that we clean up any files not
        #       part of the content. At the moment, this will add or update the files
        #       that are in the archive, but it will not delete files on the fs that are
        #       not in the archive
        files_to_extract = []
        for member in tar_members:
            # rel_path ~  roles/some-role/meta/main.yml for ex
            rel_path = member.name[len(parent_dir) + 1:]

            content_dest_root_rel_path = os.path.join(content_dest_root_path, rel_path)

            # self.log.debug('content_dest_root_path: %s', content_dest_root_path)
            # self.log.debug('content_dest_root_rel_path: %s', content_dest_root_rel_path)

            files_to_extract.append({
                'archive_member': member,
                'dest_dir': extract_to_path,
                'dest_filename': content_dest_root_rel_path,
                'force_overwrite': force_overwrite})

        file_extractor = archive.extract_files(self.tar_file, files_to_extract)

        installed_paths = [x for x in file_extractor]
        install_datetime = datetime.datetime.utcnow()

        all_installed_paths.extend(installed_paths)

        self.log.info('Extracted %s files from %s %s to %s',
                      len(all_installed_paths), self.info.archive_type, label, content_dest_root_path)

        # TODO: InstallResults object? installedPaths, InstallInfo, etc?
        return all_installed_paths, install_datetime

    def install_info(self, content_version, install_datetime):

        content_install_info = InstallInfo.from_version_date(version=content_version,
                                                             install_datetime=install_datetime)

        return content_install_info

    def install(self, repository_spec, extract_to_path, force_overwrite=False):

        all_installed_files, install_datetime = \
            self.extract(repository_spec.namespace, repository_spec.name,

                         extract_to_path, force_overwrite=force_overwrite)

        namespaced_repository_path = '%s/%s' % (repository_spec.namespace,
                                                repository_spec.name)

        info_path = os.path.join(extract_to_path,
                                 namespaced_repository_path,
                                 self.META_INSTALL)

        meta_main_path = os.path.join(extract_to_path,
                                      namespaced_repository_path,
                                      'roles',
                                      repository_spec.name,
                                      'meta',
                                      'main.yml')

        log.debug('meta_main_path: %s', meta_main_path)
        meta_main = role_metadata.load_from_filename(meta_main_path,
                                                     role_name=namespaced_repository_path)

        log.debug('meta_main: %s', meta_main)

        installed_to_path = os.path.join(extract_to_path,
                                         namespaced_repository_path)

        install_info_ = self.install_info(repository_spec.version,
                                          install_datetime=install_datetime)

        # TODO: this save will need to be moved to a step later. after validating install?
        install_info.save(install_info_, info_path)

        installation_results = InstallationResults(install_info_path=info_path,
                                                   install_info=install_info_,
                                                   installed_to_path=installed_to_path,
                                                   installed_datetime=install_datetime,
                                                   installed_files=all_installed_files,
                                                   meta_main=meta_main)
        return installation_results


@attr.s()
class TraditionalRoleContentArchive(BaseContentArchive):
    ROLES_SUBPATH = 'roles'

    def content_dest_root_subpath(self, content_namespace, content_name):
        '''Traditional role archive content goes into subpath of 'roles/CONTENT_NAME/'''
        return os.path.join(self.ROLES_SUBPATH, content_name)


@attr.s()
class CollectionContentArchive(BaseContentArchive):
    # TODO: should we create a meta/ for a collection just for .galaxy_install_info?
    META_INSTALL = os.path.join('meta', '.galaxy_install_info')


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
