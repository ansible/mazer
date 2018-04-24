
VALID_ROLE_SPEC_KEYS = [
    'name',
    'role',
    'scm',
    'src',
    'version',
]

# FIXME - need some stuff here
VALID_CONTENT_SPEC_KEYS = [

]


# Galaxy Content Constants
CONTENT_PLUGIN_TYPES = (
    'module', 'module_util', 'action_plugin', 'filter_plugin',
    'connection_plugin', 'inventory_plugin', 'lookup_plugin',
    'shell_plugin', 'strategy_plugin', 'netconf_plugin'

)
CONTENT_TYPES = CONTENT_PLUGIN_TYPES + ('role',)

# FIXME(alikins): remove dict comp for 2.6 compat
CONTENT_TYPE_DIR_MAP = {k: "%ss" % k for k in CONTENT_TYPES}


class GalaxyContentMeta(object):
    def __init__(self, name=None, version=None,
                 src=None, scm=None, content_type=None,
                 path=None, content_dir=None):
        self.name = name
        self.version = version
        self.src = src or name
        self.scm = scm
        self.content_type = content_type
        self.content_dir = content_dir
        self.path = path

    def __eq__(self, other):
        return (self.name, self.version, self.src, self.scm,
                self.content_type, self.content_dir, self.path) == \
            (self.name, self.version, self.src, self.scm,
             self.content_type, self.content_dir, self.path)
