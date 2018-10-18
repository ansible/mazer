import logging

import attr

from ansible_galaxy.models.repository_spec import RepositorySpec

log = logging.getLogger(__name__)


@attr.s(frozen=True)
class DependencySpec(RepositorySpec):
    pass
