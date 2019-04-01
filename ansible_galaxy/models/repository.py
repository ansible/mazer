import logging

import attr

from ansible_galaxy.models.repository_spec import RepositorySpec

log = logging.getLogger(__name__)


@attr.s(frozen=True)
class Repository(object):
    repository_spec = attr.ib(type=RepositorySpec)
    path = attr.ib(default=None)
    installed = attr.ib(default=False, type=bool, cmp=False)

    # ie, a collection or role-as-collections-requirement.yml
    requirements = attr.ib(factory=tuple)

    @property
    def label(self):
        return self.repository_spec.label

    def __str__(self):
        return '{repo_spec}@{path}'.format(repo_spec=self.repository_spec, path=self.path)
