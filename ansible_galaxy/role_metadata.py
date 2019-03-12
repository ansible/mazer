import logging
import os

import yaml

from ansible_galaxy import dependencies
from ansible_galaxy.models.role_metadata import RoleMetadata


log = logging.getLogger(__name__)


def load(data_or_file_object, role_name=None):
    # log.debug('loading role metadata from %s', data_or_file_object)

    # TODO: potentially want to let yaml errors bubble up more
    #       so errors have more useful info if there is yaml parse error
    data_dict = yaml.safe_load(data_or_file_object)

    # log.debug('data_dict: %s', pprint.pformat(data_dict))

    galaxy_info = data_dict.get('galaxy_info', {})

    dependencies_data = data_dict.get('dependencies', [])

    deps = dependencies.from_dependency_spec_strings(dependencies_data)

    allow_duplicates = data_dict.get('allow_duplicates', False)

    # we pass in the dir name of the role as role_name by default, but
    # can override with role_name in main.yml
    if galaxy_info.get('role_name', None):
        role_name = role_name

    role_md = RoleMetadata(name=role_name,
                           author=galaxy_info.get('author', None),
                           description=galaxy_info.get('description', None),
                           company=galaxy_info.get('company', None),
                           license=galaxy_info.get('license', None),
                           galaxy_tags=galaxy_info.get('galaxy_tags'),
                           platforms=galaxy_info.get('platforms'),
                           cloud_platforms=galaxy_info.get('cloud_platforms'),
                           min_ansible_version=galaxy_info.get('min_ansible_version'),
                           min_ansible_container_version=galaxy_info.get('min_ansible_container_version'),
                           issue_tracker=galaxy_info.get('issue_tracker_url'),
                           # from outside of galaxy_info dict
                           dependencies=deps,
                           allow_duplicates=allow_duplicates)

    # log.debug('loaded role metadata: %s', role_md)
    log.debug('loaded role metadata for %s from %s', role_name, data_or_file_object)
    return role_md


def load_from_filename(filename, role_name=None):
    log.debug('looking for content meta data from path: %s', filename)

    if not os.path.isfile(filename):
        return None

    try:
        f = open(filename, 'r')
        return load(f, role_name=role_name)
    except Exception as e:
        log.exception(e)
        log.debug('Unable to load role metadata from path: %s', filename)
        return False
    finally:
        f.close()


def load_from_dir(dirname, role_name=None):
    log.debug("Going to load role from dir %s %s", dirname, role_name or "")

    role_meta_main_filename = os.path.join(dirname, 'meta', 'main.yml')
    # role_name = '%s.%s' % (namespace, name)

    return load_from_filename(role_meta_main_filename, role_name=role_name)
