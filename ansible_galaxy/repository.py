import logging
import os
import shutil

import yaml

from ansible_galaxy import collection_info
from ansible_galaxy import install_info
from ansible_galaxy import role_metadata
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

    # load galaxy.yml
    galaxy_filename = os.path.join(path_name, collection_info.COLLECTION_INFO_FILENAME)

    collection_info_data = None

    try:
        with open(galaxy_filename, 'r') as gfd:
            collection_info_data = collection_info.load(gfd)
    except EnvironmentError:
        # log.debug('No galaxy.yml collection info found for collection %s.%s: %s', namespace, name, e)
        pass

    # Now try the repository as a role-as-collection
    # FIXME: For a repository with one role that matches the collection name and doesn't
    #        have a galaxy.yml, that's indistinguishable from a role-as-collection
    # FIXME: But in theory, if there is more than one role in roles/, we should skip this
    role_meta_main_filename = os.path.join(path_name, 'roles', name, 'meta', 'main.yml')
    role_meta_main = None
    role_name = '%s.%s' % (namespace, name)

    try:
        with open(role_meta_main_filename, 'r') as rmfd:
            role_meta_main = role_metadata.load(rmfd, role_name=role_name)
    except EnvironmentError:
        # log.debug('No meta/main.yml was loaded for repository %s.%s: %s', namespace, name, e)
        pass

    # Prefer version from install_info, but for a editable installed, there may be only galaxy version
    installed_version = install_info_version
    if collection_info_data:
        installed_version = installed_version or collection_info_data.version
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
        collection_requires = requirements.from_requirement_spec_strings(collection_info_data.dependencies,
                                                                         repository_spec=repository_spec)
        requirements_list.extend(collection_requires)

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
        log.warn('Unable to rm the directory "%s" while removing installed repo "%s": %s',
                 installed_repository.path,
                 installed_repository.label,
                 e)
        log.exception(e)
        raise
