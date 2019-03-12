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
from ansible_galaxy import role_metadata

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

    # path_name = os.path.join(content_dir, namespace, name)
    path_name = repository_archive.info.top_dir

    manifest_filename = os.path.join(path_name, collection_artifact_manifest.COLLECTION_MANIFEST_FILENAME)
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

    # load galaxy.yml
    galaxy_filename = os.path.join(path_name, collection_info.COLLECTION_INFO_FILENAME)

    collection_info_data = None

    try:
        gfd = repo_tarfile.extractfile(galaxy_filename)
        if gfd:
            collection_info_data = collection_info.load(gfd)
    except KeyError as e:
        log.warning('No %s found in archive: %s - %s', galaxy_filename, archive_path, e)
        # log.debug('No galaxy.yml collection info found for collection %s.%s: %s', namespace, name, e)

    # TODO/FIXME: what takes precedence?
    #           - the dir name in the archive that a collection lives in ~/.ansible/content/my_ns/my_name
    #           - Or the namespace/name from galaxy.yml?
    # log.debug('collection_info_data: %s', collection_info_data)

    col_info = None
    if manifest_data:
        col_info = manifest_data.collection_info
        log.debug('md.col_info: %s', col_info)
    elif collection_info_data:
        col_info = collection_info_data
    else:
        raise exceptions.GalaxyArchiveError('No galaxy collection info or manifest found in %s', archive_path)

    log.debug('col_info: %s', col_info)

    # FIXME: change collectionInfo to have separate name/namespace so we dont have to 'parse' the name
    # repo_spec = repository_spec.repository_spec_from_string(col_info.name, namespace_override=namespace)
    # spec_data = repository_spec_parse.parse_string(col_info.name)

    # log.debug('spec_data: %s', spec_data)
    # log.debug('repo_spec: %s', repo_spec)

    # Build a repository_spec of the repo now so we can pass it things like requirements.load()
    # that need to know what requires something
    # if we specify a namespace, use it otherwise use the info from galaxy.yml
    repo_spec = RepositorySpec(namespace=namespace or col_info.namespace,
                               name=col_info.name,
                               version=col_info.version,
                               spec_string=archive_path,
                               # fetch_method=None,
                               src=archive_path)

    log.debug('repo spec from %s: %r', archive_path, repo_spec)

    requirements_list = []
    requirements_list = requirements.from_requirement_spec_strings(col_info.dependencies,
                                                                   repository_spec=repo_spec)

    repository = Repository(repository_spec=repo_spec,
                            path=None,
                            installed=installed,
                            requirements=requirements_list,
                            # Assuming this is a collection artifact, FIXME if we support role artifacts
                            dependencies=[])

    log.debug('repository: %s', repository)

    return repository


def load_from_dir(content_dir, namespace, name, installed=True):
    # TODO: or artifact

    path_name = os.path.join(content_dir, namespace, name)
    # TODO: add trad role or collection detection rules here
    #       Or possibly earlier so we could call 'collection' loading
    #       code/class or trad-role-as-collection loading code/class
    #       and avoid intermingly the impls.
    #       Maybe:
    #       if more than one role in roles/ -> collection

    if not os.path.isdir(path_name):
        log.debug('The directory %s does not exist, unable to load a Repository from it', path_name)
        return None

    requirements_list = []

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

    collection_info_data = None

    try:
        with open(galaxy_filename, 'r') as gfd:
            if gfd:
                collection_info_data = collection_info.load(gfd)
    except EnvironmentError:
        # log.debug('No galaxy.yml collection info found for collection %s.%s: %s', namespace, name, e)
        pass

    # Now try the repository as a role-as-collection
    # FIXME: For a repository with one role that matches the collection name and doesn't
    #        have a galaxy.yml, that's indistinguishable from a role-as-collection
    # FIXME: But in theory, if there is more than one role in roles/, we should skip this

    role_dir_path = os.path.join(path_name, 'roles')
    role_name = '%s.%s' % (namespace, name)

    role_meta_main = role_metadata.load_from_dir(dirname=role_dir_path,
                                                 role_name=role_name)

    log.debug('role_meta_main: %s', role_meta_main)

    # Prefer version from install_info, but for a editable installed, there may be only galaxy version
    installed_version = install_info_version
    if manifest_data:
        installed_version = manifest_data.collection_info.version
    elif collection_info_data:
        installed_version = collection_info_data.version
    # if role_meta_main:
    #    installed_version = installed_version or role_meta_main.version

    # TODO/FIXME: what takes precedence?
    #           - the dir names a collection lives in ~/.ansible/content/my_ns/my_name
    #           - Or the namespace/name from galaxy.yml?
    # log.debug('collection_info_data: %s', collection_info_data)

    # Build a repository_spec of the repo now so we can pass it things like requirements.load()
    # that need to know what requires something
    repository_spec = RepositorySpec(namespace=namespace,
                                     name=name,
                                     version=installed_version)

    # The current galaxy.yml 'dependencies' are actually 'requirements' in ansible/ansible terminology
    # (ie, install-time)
    if collection_info_data:
        collection_requires = requirements.from_dependencies_dict(collection_info_data.dependencies,
                                                                  repository_spec=repository_spec)
        requirements_list.extend(collection_requires)

    # TODO: add reqs from MANIFEST.json
    # TODO: add requirements loaded from galaxy.yml
    # TODO: should the requirements in galaxy.yml be plain strings or dicts?
    # TODO: should there be requirements in galaxy.yml at all? in liue of requirements.yml
    # collection_info_requirements = []

    requirements_filename = os.path.join(path_name, 'requirements.yml')

    try:
        with open(requirements_filename, 'r') as rfd:
            requirements_list.extend(requirements.load(rfd, repository_spec=repository_spec))
    except EnvironmentError:
        # log.debug('No requirements.yml was loaded for repository %s.%s: %s', namespace, name, e)
        pass

    # TODO: if there are other places to load dependencies (ie, runtime deps) we will need
    #       to load them and combine them with role_depenency_specs

    # TODO/FIXME: load deps from MANIFEST.json if it exists (and prefer it over galaxy.yml)

    role_dependency_specs = []
    if role_meta_main:
        role_dependency_specs = role_meta_main.dependencies

    repository = Repository(repository_spec=repository_spec,
                            path=path_name,
                            installed=installed,
                            requirements=requirements_list,
                            dependencies=role_dependency_specs)

    log.debug('Repository %s loaded from %s', repository.repository_spec.label, path_name)

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
