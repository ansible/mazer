import logging

from ansible_galaxy.models.requirement import Requirement, RequirementOps, RequirementScopes
from ansible_galaxy.models.requirement_spec import RequirementSpec
from ansible_galaxy.repository_spec_parse import spec_data_from_string

log = logging.getLogger(__name__)


def from_dependencies_dict(dependencies_dict, namespace_override=None, editable=False, repository_spec=None):
    '''Build a list of Requirement objects from the 'dependencies' item in galaxy.yml'''
    reqs = []
    for req_label, req_version_spec in dependencies_dict.items():
        req_spec_data = spec_data_from_string(req_label,
                                              namespace_override=namespace_override,
                                              editable=editable)
        req_spec_data['version_spec'] = req_version_spec

        log.debug('req_spec_data: %s', req_spec_data)

        req_spec = RequirementSpec.from_dict(req_spec_data)

        log.debug('req_spec: %s', req_spec)

        requirement = Requirement(repository_spec=repository_spec, op=RequirementOps.EQ,
                                  scope=RequirementScopes.INSTALL,
                                  requirement_spec=req_spec)
        log.debug('requirement: %s', requirement)
        reqs.append(requirement)

    return reqs
