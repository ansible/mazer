import logging

import attr

log = logging.getLogger(__name__)


@attr.s
class ContentRepository(object):
    namespace = attr.ib()
    name = attr.ib()
    path = attr.ib(default=None)
    label = attr.ib(default=None)

    @property
    def label(self):
        return '%s.%s' % (self.namespace.namespace, self.name)
