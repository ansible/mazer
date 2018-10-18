import logging

from ansible_galaxy.models.dependency import DependencySpec
from ansible_galaxy.repository_spec import spec_data_from_string

log = logging.getLogger(__name__)


def from_dependency_spec_strings(dependency_spec_strings, namespace_override=None, editable=False):
    dep_specs = []
    for dep_spec_string in dependency_spec_strings:
        dep_spec_data = spec_data_from_string(dep_spec_string)

        log.debug('dep_spec_data: %s', dep_spec_data)

        dep_spec = DependencySpec.from_dict(dep_spec_data)

        log.debug('dep_spec: %s', dep_spec)
        dep_specs.append(dep_spec)

    return dep_specs
