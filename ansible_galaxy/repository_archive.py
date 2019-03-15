import datetime
import logging
import os
import tarfile

from ansible_galaxy import archive
from ansible_galaxy import collection_members
from ansible_galaxy import exceptions
from ansible_galaxy import install_info
from ansible_galaxy.models import content
from ansible_galaxy.models.repository_archive import RepositoryArchiveInfo, CollectionRepositoryArchive
from ansible_galaxy.models.repository_archive import CollectionRepositoryArtifactArchive, TraditionalRoleRepositoryArchive
from ansible_galaxy.models.repository_spec import FetchMethods
from ansible_galaxy.models.install_info import InstallInfo
from ansible_galaxy.models.installation_results import InstallationResults

log = logging.getLogger(__name__)

# TODO: better place to define?
META_MAIN = os.path.join('meta', 'main.yml')
GALAXY_FILE = 'ansible-galaxy.yml'
APB_YAML = 'apb.yml'


def null_display_callback(*args, **kwargs):
    log.debug('display_callback: %s', args)


def extract(repository_spec,
            repository_archive_info,
            content_path,
            extract_archive_to_dir,
            tar_file,
            force_overwrite=False,
            display_callback=None):

    all_installed_paths = []

    # TODO: move to content info validate step in install states?
    if not repository_spec.namespace:
        # TODO: better error
        raise exceptions.GalaxyError('While installing a role , no namespace was found. Try providing one with --namespace')

    # label = "%s.%s" % (repository_namespace, repository_name)

    # 'extract_to_path' is for ex, ~/.ansible/content
    log.debug('About to extract %s "%s" to %s', repository_archive_info.archive_type,
              repository_spec.label, content_path)
    # display_callback('- extracting %s repository from "%s"' % (repository_archive_info.archive_type,
    #                                                           repository_spec.label))

    tar_members = tar_file.members

    # self.log.debug('content_dest_root_subpath: %s', content_dest_root_subpath)

    # self.log.debug('content_dest_root_path1: |%s|', content_dest_root_path)

    # TODO: need to support deleting all content in the dirs we are targetting
    #       first (and/or delete the top dir) so that we clean up any files not
    #       part of the content. At the moment, this will add or update the files
    #       that are in the archive, but it will not delete files on the fs that are
    #       not in the archive
    files_to_extract = []
    for member in tar_members:
        rel_path = member.name

        extract_to_filename_path = os.path.join(extract_archive_to_dir, rel_path)

        # self.log.debug('content_dest_root_path: %s', content_dest_root_path)
        # self.log.debug('content_dest_root_rel_path: %s', content_dest_root_rel_path)

        files_to_extract.append({
            'archive_member': member,
            # Note: for trad roles, we are extract the top level of the archive into
            #       a sub path of the destination
            'dest_dir': extract_archive_to_dir,
            'dest_filename': extract_to_filename_path,
            'force_overwrite': force_overwrite})

    file_extractor = archive.extract_files(tar_file, files_to_extract)

    installed_paths = [x for x in file_extractor]

    all_installed_paths.extend(installed_paths)

    log.debug('Extracted %s files from %s %s to %s',
              len(all_installed_paths),
              repository_archive_info.archive_type,
              repository_spec.label,
              extract_archive_to_dir)

    # TODO: InstallResults object? installedPaths, InstallInfo, etc?
    return all_installed_paths


def detect_repository_archive_type(archive_path, file_names):
    '''Try to determine if we are a role, multi-content, apb etc.

    if there is a meta/main.yml ->  role

    if there is any of the content types subdirs -> multi-content'''

    # FIXME: just looking for the root dir...

    top_dir = file_names[0]

    # log.debug('top_dir of %s: %s', archive_path, top_dir)

    meta_main_target = os.path.join(top_dir, 'meta/main.yml')
    manifest_path = os.path.join(top_dir, 'MANIFEST.json')

    type_dirs = content.CONTENT_TYPE_DIR_MAP.values()
    # log.debug('type_dirs: %s', type_dirs)

    type_dir_targets = set([os.path.join(top_dir, x) for x in type_dirs])
    # log.debug('type_dir_targets: %s', type_dir_targets)

    has_manifest = any([member for member in file_names if member == manifest_path])
    log.debug('has_manifest: %s', has_manifest)

    for member in file_names:
        if member == meta_main_target:
            return 'role'

    for member in file_names:
        if member in type_dir_targets:
            if has_manifest:
                return 'multi-content-artifact'
            return 'multi-content'

    # otherwise, assume it is a collection / multi-content repo archive
    return 'multi-content'


def build_archive_info(archive_path, file_names):
    archive_parent_dir = None
    archive_parent_dir = file_names[0]

    archive_type = detect_repository_archive_type(archive_path, file_names)

    # log.debug('archive_type of %s: %s', archive_path, archive_type)
    # log.debug("archive_parent_dir of %s: %s", archive_path, archive_parent_dir)

    # looks like we are a role, update the default content_type from all -> role
    if archive_type == 'role':
        log.debug('Found role metadata in the archive %s, so installing it as role content_type',
                  archive_path)

    archive_info = RepositoryArchiveInfo(top_dir=archive_parent_dir,
                                         archive_type=archive_type,
                                         archive_path=archive_path)

    return archive_info


def load_editable_archive_info(archive_path, repository_spec):
    file_walker = collection_members.FileWalker(collection_path=archive_path)
    col_members = collection_members.CollectionMembers(walker=file_walker)
    file_members = list(col_members.run())

    archive_info = build_archive_info(archive_path, file_members)

    return archive_info, None


def load_tarfile_archive_info(archive_path, repository_spec):

    # if not tarfile.is_tarfile(archive_path):
    #    raise exceptions.GalaxyClientError("the file downloaded was not a tar.gz")

    if archive_path.endswith('.gz'):
        tar_flags = "r:gz"
    else:
        tar_flags = "r"

    try:
        repository_tar_file = tarfile.open(archive_path, tar_flags)
    except tarfile.TarError as e:
        log.exception(e)
        raise exceptions.GalaxyClientError("Error opening the tar file %s with flags: %s for repo: %s" %
                                           (archive_path, tar_flags, repository_spec))

    members = repository_tar_file.getmembers()
    archive_info = build_archive_info(archive_path, [m.name for m in members])

    # log.debug('role archive_info for %s: %s', archive_path, archive_info)

    return archive_info, repository_tar_file


def load_archive_info(archive_path, repository_spec=None):

    # "installing" an existing dir as editable
    if repository_spec and repository_spec.fetch_method == FetchMethods.EDITABLE:
        return load_editable_archive_info(archive_path, repository_spec)

    return load_tarfile_archive_info(archive_path, repository_spec)


def load_archive(archive_path, repository_spec=None):
    '''Load the archive file at archive_path and return a RepositoryArchive'''
    # To avoid opening the archive file twice, and since we have to open/load it to
    # get the archive_info, we also return it from load_archive_info
    archive_info, tar_file = load_archive_info(archive_path, repository_spec)

    # factory-ish
    if archive_info.archive_type in ['role']:
        repository_archive_ = TraditionalRoleRepositoryArchive(info=archive_info,
                                                               tar_file=tar_file)
    elif archive_info.archive_type == 'multi-content-artifact':
        repository_archive_ = CollectionRepositoryArtifactArchive(info=archive_info,
                                                                  tar_file=tar_file)
    else:
        repository_archive_ = CollectionRepositoryArchive(info=archive_info,
                                                          tar_file=tar_file)

    log.debug('repository archive_ for %s: %s', archive_path, repository_archive_)

    return repository_archive_


def install(repository_archive, repository_spec, destination_info, display_callback):
    log.debug('installing/extracting repo archive %s to destination %s', repository_archive, destination_info)

    # An editable install is a symlink to existing dir, so nothing to extract
    if destination_info.editable:
        all_installed_files = []
    else:
        all_installed_files = extract(repository_spec,
                                      repository_archive.info,
                                      content_path=destination_info.destination_root_dir,
                                      extract_archive_to_dir=destination_info.extract_archive_to_dir,
                                      tar_file=repository_archive.tar_file,
                                      display_callback=display_callback)

    install_datetime = datetime.datetime.utcnow()

    install_info_ = InstallInfo.from_version_date(repository_spec.version,
                                                  install_datetime=install_datetime)

    # TODO: this save will need to be moved to a step later. after validating install?
    # The to_dict_version_strings is to convert the un-yaml-able semantic_version.Version to a string
    install_info.save(install_info_.to_dict_version_strings(),
                      destination_info.install_info_path)

    installation_results = InstallationResults(install_info_path=destination_info.install_info_path,
                                               install_info=install_info_,
                                               installed_to_path=destination_info.path,
                                               installed_datetime=install_datetime,
                                               installed_files=all_installed_files)
    return installation_results
