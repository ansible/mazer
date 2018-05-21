# equiv to ansible.constants

# config data that is set at runtime (as opposed to defaults
# and constants)

# FIXME: replace with something backed with config files etc

# no default?
GALAXY_ROLE_SKELETON = None
GALAXY_SERVER = "https://galaxy-qa.ansible.com"
GALAXY_IGNORE_CERTS = False
GALAXY_ROLE_SKELETON_IGNORE = ["^.git$", "^.*/.git_keep$"]
GALAXY_TOKEN = None

# FIXME: replace with something namespace
# FIXME: replace with enums
COLOR_CHANGED = "yellow"
COLOR_DEBUG = "dark gray"
COLOR_DEPRECATE = "purple"
COLOR_ERROR = "red"
COLOR_VERBOSE = "blue"
COLOR_WARN = "bright purple"
COLOR_OK = "green"

# FIXME:
# The CONFIG_FILE to use is a config option?
CONFIG_FILE = None
