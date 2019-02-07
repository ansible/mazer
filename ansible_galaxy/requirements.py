import logging

import semantic_version
import yaml

from ansible_galaxy.models.requirement import Requirement, RequirementOps, RequirementScopes
from ansible_galaxy.models.requirement_spec import RequirementSpec
from ansible_galaxy.repository_spec import spec_data_from_string
from ansible_galaxy.utils import yaml_parse

log = logging.getLogger(__name__)


def load(data_or_file_object, repository_spec=None):
    log.debug('START of load of requirements %s', data_or_file_object.name)

    requirements_data = yaml.safe_load(data_or_file_object)

    # log.debug('requirements_data: %s', pprint.pformat(requirements_data))

    requirements_list = []

    for req_data_item in requirements_data:
        # log.debug('req_data_item: %s', req_data_item)
        # log.debug('type(req_data_item): %s', type(req_data_item))

        req_spec_data = yaml_parse.yaml_parse(req_data_item)

        # FIXME: find a better place to do this
        # create a version_spec from the 'version' field, a requiremenst.yml
        # does not currently expect to have a 'version_spec' data in it
        version_spec_str = '*'
        version_str = req_spec_data.pop('version')

        if version_str:
            version_spec_str = '==%s' % version_str

        version_spec = semantic_version.Spec(version_spec_str)

        req_spec_data['version_spec'] = version_spec

        # log.debug('data_name (after): %s', data_name)
        # log.debug('name_info: %s', name_info)

        req_spec = RequirementSpec.from_dict(req_spec_data)

        # log.debug('req_spec: %s', req_spec)

        req = Requirement(repository_spec=repository_spec, op=RequirementOps.EQ, requirement_spec=req_spec)

        # log.debug('req: %s', req)

        requirements_list.append(req)

    log.debug('FINISH of load of requirements: %s: %s', data_or_file_object.name, requirements_list)
    return requirements_list


def from_dependencies_dict(dependencies_dict, namespace_override=None, editable=False, repository_spec=None):
    '''Build a list of Requirement objects from the 'dependencies' item in galaxy.yml'''
    reqs = []
    for req_label, req_version_spec in dependencies_dict.items():
        req_spec_data = spec_data_from_string(req_label,
                                              namespace_override=namespace_override,
                                              editable=editable)
        req_spec_data['version_spec'] = req_version_spec
        req_spec_data['req_spec_string'] = req_spec_data.pop('spec_string', None)

        log.debug('req_spec_data: %s', req_spec_data)

        req_spec = RequirementSpec.from_dict(req_spec_data)

        log.debug('req_spec: %s', req_spec)

        requirement = Requirement(repository_spec=repository_spec, op=RequirementOps.EQ,
                                  scope=RequirementScopes.INSTALL,
                                  requirement_spec=req_spec)
        log.debug('requirement: %s', requirement)
        reqs.append(requirement)

    return reqs


def from_requirement_spec_strings(requirement_spec_strings, namespace_override=None, editable=False, repository_spec=None):
    reqs = []
    for requirement_spec_string in requirement_spec_strings:
        req_spec_data = spec_data_from_string(requirement_spec_string,
                                              namespace_override=namespace_override,
                                              editable=editable)

        req_spec = RequirementSpec.from_dict(req_spec_data)

        req = Requirement(repository_spec=repository_spec, op=RequirementOps.EQ, requirement_spec=req_spec)

        reqs.append(req)

    return reqs
