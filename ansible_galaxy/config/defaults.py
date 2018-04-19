
# NOTE: string but ansible parses path spec
# FIXME: just make a list. Add a patchspec type?
DEFAULT_ROLES_PATH = ['~/.ansible/roles', '/usr/share/ansible/roles', '/etc/ansible/roles']
DEFAULT_MODULE_PATH = ['~/.ansible/plugins/modules', '/usr/share/ansible/plugins/modules']
DEFAULT_CONTENT_PATH = ['~/.ansible/content', '/usr/share/ansible/content']

# FIXME: dunno yet

DEFAULT_LOCAL_TMP = "~/.ansible/tmp"

# FIXME: replace with logging config
DEFAULT_LOG_PATH = ''
DEFAULT_LOG_FILTER = []
DEFAULT_DEBUG = True
DEFAULT_VERBOSITY = 0
