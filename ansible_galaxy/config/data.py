# a data object representing the run time config of ansible-galaxy

import collections
import logging

# TODO: runtime can go away once config works
from ansible_galaxy.config import runtime
from ansible_galaxy.config import yaml_file
from ansible_galaxy import exceptions

# import yaml_config_load, config_save

log = logging.getLogger(__name__)

# a list of tuples that is fed to an OrderedDict
DEFAULTS = [
    # defaults ?
    ('defaults', {}),

    #
    ('servers',  [
        {'url': runtime.GALAXY_SERVER,
         'ignore_certs': runtime.GALAXY_IGNORE_CERTS,
         'token': runtime.GALAXY_TOKEN,
         },
    ]),

    # In order of priority
    ('content_roots', [
        '~/.ansible/content',
        '/usr/share/ansible/content',
    ]),

    # runtime options
    ('options', {
        'role_skeleton_path': None,
        'role_skeleton_ignore': ["^.git$", "^.*/.git_keep$"],
    }),
    ('version', 1),
]

_default_conf_data = collections.OrderedDict(DEFAULTS)


# TODO: cache?  ideally, should only ever call this once per process
def config_load(file_path=None):

    try:
        conf_data = yaml_file.config_load(file_path=file_path)
    except OSError as e:
        log.exception(e)
        log.error('Unable to load config file (%s): %s', file_path, e)
        log.warn('Using default config data instead of (%s)', file_path)
        return _default_conf_data
    except Exception as e:
        log.exception(e)
        log.error('Unable to load and parse config file (%s): %s', file_path, e)
        raise exceptions.GalaxyConfigError(e)

    return conf_data


def config_save(conf_data, file_path=None):
    try:
        yaml_file.config_save(conf_data, file_path=file_path)
    except Exception as e:
        log.exception(e)
        log.error('Unable to save config file (%s): %s', file_path, e)
