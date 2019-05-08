import logging
import os
import shutil

import yaml

from ansible_galaxy import collection_info
from ansible_galaxy import collection_artifact_manifest
# from ansible_galaxy import collection_artifact_file_manifest
from ansible_galaxy import exceptions
from ansible_galaxy import install_info
from ansible_galaxy import requirements

from ansible_galaxy.models.repository_spec import RepositorySpec
from ansible_galaxy.models.repository import Repository

log = logging.getLogger(__name__)

# TODO: This loads a full repository object from disk. But that can
#       can be slow. Will likely need some sort of 'Summary' (to use cargo's term)
#       object that is just the important stuff (possibly cached somewhere?)
# aka, persistence of ansible_galaxy.models.repository


def load(data_or_file_object):
    repository_data = yaml.safe_load(data_or_file_object)
    return repository_data


def load_from_archive(repository_archive, namespace=None, installed=True):
    repo_tarfile = repository_archive.tar_file
    archive_path = repository_archive.info.archive_path

    manifest_filename = os.path.join(collection_artifact_manifest.COLLECTION_MANIFEST_FILENAME)
    manifest_data = None

    log.debug('Trying to extract %s from %s', manifest_filename, archive_path)

    try:
        mfd = repo_tarfile.extractfile(manifest_filename)
        if mfd:
            manifest_data = collection_artifact_manifest.load(mfd)
            log.debug('md: %s', manifest_data)
            log.debug('md.collection_info: %s', manifest_data.collection_info)
            log.debug('manifest_data.collection_info.name: %s', manifest_data.collection_info.name)
    except KeyError as e:
        log.warning('No %s found in archive: %s (Error: %s)', manifest_filename, archive_path, e)

    if not manifest_data:
        raise exceptions.GalaxyArchiveError('No collection manifest (%s) found in %s' % (collection_artifact_manifest.COLLECTION_MANIFEST_FILENAME,
                                                                                         archive_path),
                                            archive_path=archive_path)

    col_info = manifest_data.collection_info

    log.debug('col_info: %s', col_info)

    # if we specify a namespace, use it otherwise use the info from the manifest col_info
    repo_spec = RepositorySpec(namespace=namespace or col_info.namespace,
                               name=col_info.name,
                               version=col_info.version,
                               spec_string=archive_path,
                               # fetch_method=None,
                               src=archive_path)

    log.debug('repo spec from %s: %r', archive_path, repo_spec)

    requirements_list = requirements.from_dependencies_dict(col_info.dependencies,
                                                            repository_spec=repo_spec)

    repository = Repository(repository_spec=repo_spec,
                            path=None,
                            installed=installed,
                            requirements=requirements_list,)

    log.debug('repository: %s', repository)

    return repository


# TODO: rename load_from_dir_in_namespace()?
# TODO: simplify this, rename as part of Repository->Collection re-re-naming
def load_from_dir(content_dir, namespace_path, namespace, name, installed=True):
    path_name = os.path.join(namespace_path, name)

    log.debug('Loading repository %s.%s from path: %s', namespace, name, path_name)

    if not os.path.isdir(path_name):
        log.debug('The directory %s does not exist, unable to load a Repository from it', path_name)
        return None

    # Now look for any install_info for the repository
    install_info_data = None
    install_info_filename = os.path.join(path_name, 'meta/.galaxy_install_info')

    try:
        with open(install_info_filename, 'r') as ifd:
            install_info_data = install_info.load(ifd)
    except EnvironmentError as e:
        log.warning('Unable to find or load meta/.galaxy_install_info for repository %s.%s: %s', namespace, name, e)

    # TODO: figure out what to do if the version from install_info conflicts with version
    #       from galaxy.yml etc.
    install_info_version = getattr(install_info_data, 'version', None)

    # Try to load a MANIFEST.json if we have one

    manifest_filename = os.path.join(path_name, collection_artifact_manifest.COLLECTION_MANIFEST_FILENAME)
    manifest_data = None

    try:
        with open(manifest_filename, 'r') as mfd:
            manifest_data = collection_artifact_manifest.load(mfd)
    except EnvironmentError:
        # log.debug('No galaxy.yml collection info found for collection %s.%s: %s', namespace, name, e)
        pass

    # # TODO/FIXME: do we even need to load file_manifest here?
    # file_manifest_filename = os.path.join(path_name, collection_artifact_file_manifest.COLLECTION_FILE_MANIFEST_FILENAME)
    # file_manifest_data = None

    # try:
    #     with open(file_manifest_filename, 'r') as mfd:
    #         file_manifest_data = collection_artifact_file_manifest.load(mfd)
    # except EnvironmentError:
    #     # log.debug('No galaxy.yml collection info found for collection %s.%s: %s', namespace, name, e)
    #     pass

    # load galaxy.yml
    galaxy_filename = os.path.join(path_name, collection_info.COLLECTION_INFO_FILENAME)

    galaxy_yml_data = None

    try:
        with open(galaxy_filename, 'r') as gfd:
            if gfd:
                galaxy_yml_data = collection_info.load(gfd)
    except EnvironmentError:
        # for the case of collections that are not from or intended for galaxy, they do not
        # need to provide a galaxy.yml or MANIFEST.json, so an error here is exceptable.
        # log.debug('No galaxy.yml collection info found for collection %s.%s: %s', namespace, name, e)
        pass

    # TODO: make existence of a galaxy.yml and a MANIFEST.json mutual exclude and raise an exception for that case

    col_info = None
    # MANIFEST.json is higher prec than galaxy.yml
    if galaxy_yml_data:
        col_info = galaxy_yml_data

    if manifest_data:
        col_info = manifest_data.collection_info

    # Prefer version from install_info, but for a editable installed, there may be only galaxy version
    installed_version = install_info_version
    if col_info:
        installed_version = col_info.version

    # TODO/FIXME: what takes precedence?
    #           - the dir names a collection lives in ~/.ansible/content/my_ns/my_name
    #           - Or the namespace/name from galaxy.yml?
    #           - Or the namespace/name from MANIFEST.json
    #         Ditto for requirements

    # log.debug('collection_info_data: %s', collection_info_data)

    # Build a repository_spec of the repo now so we can pass it things like
    # requirements.from_dependencies_dict that need to know what requires something.
    repository_spec = RepositorySpec(namespace=namespace,
                                     name=name,
                                     version=installed_version)

    # The current galaxy.yml 'dependencies' are actually 'requirements' in ansible/ansible terminology
    # (ie, install-time)
    requirements_list = []
    if col_info:
        requirements_list = requirements.from_dependencies_dict(col_info.dependencies,
                                                                repository_spec=repository_spec)

    repository = Repository(repository_spec=repository_spec,
                            path=path_name,
                            installed=installed,
                            requirements=requirements_list,)

    log.debug('Loaded repository %s from %s', repository.repository_spec.label, path_name)

    return repository


def remove(installed_repository):
    log.info("Removing installed repository: %s", installed_repository)

    # editable installs are symlinks
    if os.path.islink(installed_repository.path):
        log.info('Removing the symlink at %s to %s',
                 installed_repository.path,
                 os.readlink(installed_repository.path))
        os.unlink(installed_repository.path)
        return True

    try:
        shutil.rmtree(installed_repository.path)
        return True
    except EnvironmentError as e:
        log.warning('Unable to rm the directory "%s" while removing installed repo "%s": %s',
                    installed_repository.path,
                    installed_repository.label,
                    e)
        log.exception(e)
        raise
