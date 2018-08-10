import logging

import attr

log = logging.getLogger(__name__)


@attr.s(frozen=True)
class BuildContext(object):
    collection_src_root = attr.ib()
    output_path = attr.ib()
