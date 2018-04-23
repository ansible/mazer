
from ansible_galaxy.exceptions import GalaxyError


class GalaxyCliError(GalaxyError):
    pass


# replacement for AnsibleOptionError
# FIXME: CliOptionError (singular Option) ?
class CliOptionsError(Exception):
    pass
