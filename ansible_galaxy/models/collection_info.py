
import logging

import attr

log = logging.getLogger(__name__)


# see https://github.com/ansible/galaxy/issues/957
@attr.s(frozen=True)
class CollectionInfo(object):
    namespace = attr.ib()
    name = attr.ib()
    version = attr.ib()
    format_version = attr.ib(default=0.0)
    author = attr.ib(default=None)
    license = attr.ib(default=None)
