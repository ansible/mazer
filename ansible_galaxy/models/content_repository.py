import logging

import attr

log = logging.getLogger(__name__)


@attr.s
class ContentRepository(object):
    content_spec = attr.ib()
    path = attr.ib(default=None)
