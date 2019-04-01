import logging

from ansible_galaxy.models.requirement import Requirement, RequirementOps, RequirementScopes
from ansible_galaxy.models.requirement_spec import RequirementSpec
from ansible_galaxy.repository_spec_parse import spec_data_from_string

log = logging.getLogger(__name__)


def from_dependency_spec_strings(dependency_spec_strings, namespace_override=None, editable=False):
    deps = []
    for dep_spec_string in dependency_spec_strings:
        dep_spec_data = spec_data_from_string(dep_spec_string)

        log.debug('dep_spec_data: %s', dep_spec_data)

        dep_spec = RequirementSpec.from_dict(dep_spec_data)

        log.debug('dep_spec: %s', dep_spec)

        # Add a requirement, but with the 'RUNTIME' scope
        requirement = Requirement(repository_spec=None, op=RequirementOps.EQ,
                                  scope=RequirementScopes.RUNTIME,
                                  requirement_spec=dep_spec)
        deps.append(requirement)

    return deps
