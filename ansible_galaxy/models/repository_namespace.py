
import logging

import attr

log = logging.getLogger(__name__)

# TODO: use 'attr' or similar


@attr.s(frozen=True)
class RepositoryNamespace(object):
    namespace = attr.ib()
    path = attr.ib(default=None, cmp=False)
