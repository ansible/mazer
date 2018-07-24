import logging
import pprint

import yaml

from ansible_galaxy.models.role_metadata import RoleMetadata

log = logging.getLogger(__name__)


def load(data_or_file_object, role_name=None):
    log.debug('loading role metadata from %s', data_or_file_object)

    data_dict = yaml.safe_load(data_or_file_object)

    log.debug('data_dict: %s', pprint.pformat(data_dict))

    galaxy_info = data_dict.get('galaxy_info', {})
    dependencies = data_dict.get('dependencies', [])
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
                           # from outside of galaxy_info dict
                           dependencies=dependencies,
                           allow_duplicates=allow_duplicates)

    log.debug('loaded role metadata: %s', role_md)
    return role_md
