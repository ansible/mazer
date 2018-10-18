import logging

import attr

from ansible_galaxy.models.install_info import InstallInfo
from ansible_galaxy.models.role_metadata import RoleMetadata

log = logging.getLogger(__name__)


VALID_ROLE_SPEC_KEYS = [
    'src',
    'version',
    'role',
    'name',
    'scm',
]

# Galaxy Content Constants
CONTENT_PLUGIN_TYPES = (
    'module',
    'module_util',
    'plugin'
)
CONTENT_TYPES = CONTENT_PLUGIN_TYPES + ('role',)
SUPPORTED_CONTENT_TYPES = CONTENT_TYPES

CONTENT_TYPE_DIR_MAP = dict([(k, '%ss' % k) for k in CONTENT_TYPES])
TYPE_DIR_CONTENT_TYPE_MAP = dict([('%ss' % k, k) for k in CONTENT_TYPES])


@attr.s(frozen=True)
class Content(object):
    namespace = attr.ib()
    name = attr.ib()
    version = attr.ib()
    # content_type = attr.ib()
    requirements = attr.ib(factory=list)
    dependencies = attr.ib(factory=list)

    meta_main = attr.ib(default=None, type=RoleMetadata)

    src = attr.ib(default=None)
    scm = attr.ib(default=None)
    content_dir = attr.ib(default=None)
    path = attr.ib(default=None)

    requires_meta_main = attr.ib(default=None, cmp=False)
    content_sub_dir = attr.ib(default=None, cmp=False)

    @classmethod
    def from_data(cls, data):
        inst = cls(**data)
        return inst

