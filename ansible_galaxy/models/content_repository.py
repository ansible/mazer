import logging

import attr

log = logging.getLogger(__name__)


@attr.s
class ContentRepository(object):
    content_spec = attr.ib()
    # path = attr.ib(default=None)


@attr.s
class InstalledContentRepository(object):
    content_spec = attr.ib()
    path = attr.ib(default=None)
