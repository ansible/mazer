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

log.setLevel(logging.INFO)
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

    # if not os.path.isdir(path_name):
    #    log.debug('No collection found at %s', path_name)
    #    return None

    # load galaxy.yml
    galaxy_filename = os.path.join(path_name, collection_info.COLLECTION_INFO_FILENAME)

    collection_info_data = None
    try:
        with open(galaxy_filename, 'r') as gfd:
            collection_info_data = collection_info.load(gfd)
    except EnvironmentError as e:
        log.warning('No galaxy.yml found for collection %s.%s: %s', namespace, name, e)
        # log.exception(e)

    log.debug('collection_info_data: %s', collection_info_data)

    requirements_filename = os.path.join(path_name, 'requirements.yml')
    requirements_list = []

    try:
        with open(requirements_filename, 'r') as rfd:
            # requirements_data = yaml.safe_load(rfd)
            requirements_list = requirements.load(rfd)
    except EnvironmentError as e:
        log.warning('No requirements.yml found for collection %s.%s: %s', namespace, name, e)

    log.debug('requirements_list: %s', requirements_list)

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
    except EnvironmentError as e:
        log.warning('Unable to find or load meta/main.yml for repository %s.%s: %s', namespace, name, e)

    # TODO: if there are other places to load dependencies (ie, runtime deps) we will need
    #       to load them and combine them with role_depenency_specs
    role_dependency_specs = []
    if role_meta_main:
        log.debug('role_meta_main: %s', role_meta_main)
        log.debug('role_meta_main_deps: %s', role_meta_main.dependencies)
        role_dependency_specs = role_meta_main.dependencies

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
    log.debug('install_info: %s', install_info_data)
    install_info_version = getattr(install_info_data, 'version', None)

    repository_spec = RepositorySpec(namespace=namespace,
                                     name=name,
                                     version=install_info_version)

    repository = Repository(repository_spec=repository_spec,
                            path=path_name,
                            installed=installed,
                            requirements=requirements_list,
                            dependencies=role_dependency_specs)

    log.debug('repository: %s', repository)

    return repository


def remove(installed_repository):
    log.info("Removing installed repository: %s", installed_repository)
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
