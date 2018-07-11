import logging

import attr

log = logging.getLogger(__name__)


VALID_ROLE_SPEC_KEYS = [
    'src',
    'version',
    'role',
    'name',
    'scm',
]

# FIXME - need some stuff here
VALID_CONTENT_SPEC_KEYS = [

]


# Galaxy Content Constants
CONTENT_PLUGIN_TYPES = (
    'module',
    'module_util',
    'action_plugin',
    'apb',
    'filter_plugin',
    'connection_plugin',
    'inventory_plugin',
    'lookup_plugin',
    'shell_plugin',
    'strategy_plugin',
    'netconf_plugin',
    'callback_plugin',
)
CONTENT_TYPES = CONTENT_PLUGIN_TYPES + ('role',)
SUPPORTED_CONTENT_TYPES = ('role',)

CONTENT_TYPE_DIR_MAP = dict([(k, '%ss' % k) for k in CONTENT_TYPES])
CONTENT_TYPE_DIR_MAP['module'] = 'library'
TYPE_DIR_CONTENT_TYPE_MAP = dict([('%ss' % k, k) for k in CONTENT_TYPES])
TYPE_DIR_CONTENT_TYPE_MAP['library'] = 'module'


@attr.s(frozen=True)
class GalaxyContentMeta(object):
    namespace = attr.ib()
    name = attr.ib()
    version = attr.ib()
    content_type = attr.ib()
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


class GalaxyContent(object):
    def __init__(self):
        # need class for obj for ansible-galaxy.yml metadata file
        self.galaxy_metadata = {}
        # or instance of some InstallInfo class
        self.install_info = {}
        # or instance of GalaxyContentMeta
        self.content_meta = {}
