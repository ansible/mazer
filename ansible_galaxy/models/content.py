
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
