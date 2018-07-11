import logging

import attr

from ansible_galaxy.models.content_spec import ContentSpec

log = logging.getLogger(__name__)


@attr.s(frozen=True)
class ContentRepository(object):
    content_spec = attr.ib(type=ContentSpec)
    path = attr.ib(default=None)
    installed = attr.ib(default=False, type=bool, cmp=False)
