import datetime
import logging
import os
import tarfile

from ansible_galaxy import archive
from ansible_galaxy import collection_members
from ansible_galaxy import exceptions
from ansible_galaxy import install_info
from ansible_galaxy.models.collection_artifact_archive import CollectionArtifactArchiveInfo
from ansible_galaxy.models.collection_artifact_archive import CollectionArtifactArchive
from ansible_galaxy.models.repository_spec import FetchMethods
from ansible_galaxy.models.install_info import InstallInfo
from ansible_galaxy.models.installation_results import InstallationResults

log = logging.getLogger(__name__)


# TODO: extract_archive_to_dir may not be needed now (was for roles)
def extract(repository_spec,
            collections_path,
            extract_archive_to_dir,
            tar_file,
            force_overwrite=False,
            display_callback=None):

    all_installed_paths = []

    # TODO: move to content info validate step in install states?
    if not repository_spec.namespace:
        # TODO: better error
        raise exceptions.GalaxyError('While installing a collection , no namespace was found. Try providing one with --namespace')

    log.debug('About to extract "%s" to collections_path %s', repository_spec.label, collections_path)

    tar_members = tar_file.members

    # TODO: need to support deleting all content in the dirs we are targetting
    #       first (and/or delete the top dir) so that we clean up any files not
    #       part of the content. At the moment, this will add or update the files
    #       that are in the archive, but it will not delete files on the fs that are
    #       not in the archive
    files_to_extract = []
    for member in tar_members:
        rel_path = member.name

        extract_to_filename_path = os.path.join(extract_archive_to_dir, rel_path)

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

    log.debug('Extracted %s files from %s to %s',
              len(all_installed_paths),
              repository_spec.label,
              extract_archive_to_dir)

    # TODO: InstallResults object? installedPaths, InstallInfo, etc?
    return all_installed_paths


def build_archive_info(archive_path, file_names):
    archive_parent_dir = file_names[0]

    archive_type = "multi-content-artifact"

    archive_info = CollectionArtifactArchiveInfo(top_dir=archive_parent_dir,
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

    return archive_info, repository_tar_file


def load_archive_info(archive_path, repository_spec=None):

    # "installing" an existing dir as editable
    if repository_spec and repository_spec.fetch_method == FetchMethods.EDITABLE:
        return load_editable_archive_info(archive_path, repository_spec)

    return load_tarfile_archive_info(archive_path, repository_spec)


def load_archive(archive_path, repository_spec=None):
    '''Load the archive file at archive_path and return a CollectionRepositoryArtifactArchive'''
    # To avoid opening the archive file twice, and since we have to open/load it to
    # get the archive_info, we also return it from load_archive_info
    archive_info, tar_file = load_archive_info(archive_path, repository_spec)

    repository_archive_ = CollectionArtifactArchive(info=archive_info,
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
                                      collections_path=destination_info.collections_path,
                                      extract_archive_to_dir=destination_info.path,
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
