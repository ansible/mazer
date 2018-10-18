import logging

import attr

from ansible_galaxy.models.repository_spec import RepositorySpec

log = logging.getLogger(__name__)


@attr.s(frozen=True)
class Repository(object):
    repository_spec = attr.ib(type=RepositorySpec)
    path = attr.ib(default=None)
    installed = attr.ib(default=False, type=bool, cmp=False)

    # ie, a role-as-collections-meta-main-deps
    dependencies = attr.ib(factory=list)

    # ie, a collection or role-as-collections-requirement.yml
    requirements = attr.ib(factory=list)

    @property
    def label(self):
        return self.repository_spec.label
