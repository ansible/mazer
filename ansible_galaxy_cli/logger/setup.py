"""Setup default logging"""

import logging
import logging.config
import os

LOG_FILE = os.path.expandvars(os.path.expanduser('~/.ansible/ansible-galaxy-cli.log')),

DEFAULT_CONSOLE_LEVEL = os.getenv('GALAXY_CLI_LOG_LEVEL', 'WARNING').upper()
DEFAULT_LEVEL = 'DEBUG'

DEFAULT_DEBUG_FORMAT = '[%(asctime)s,%(msecs)03d %(process)05d %(levelname)-0.1s] %(name)s %(funcName)s:%(lineno)d - %(message)s'
# DEFAULT_HANDLERS = ['console', 'file']
DEFAULT_HANDLERS = ['file']

DEFAULT_LOGGING_CONFIG = {
    'version': 1,

    'disable_existing_loggers': False,

    'formatters': {
        # skip the date for console log handler, but include it for the file log handler
        'console_verbose': {
            'format': DEFAULT_DEBUG_FORMAT,
            'datefmt': '%H:%M:%S',
        },
        'file_verbose': {
            'format': '[%(asctime)s %(process)05d %(levelname)-0.1s] %(name)s %(funcName)s:%(lineno)d - %(message)s',
        },
    },

    'filters': {},

    'handlers': {
        'console': {
            'level': DEFAULT_CONSOLE_LEVEL,
            'class': 'logging.StreamHandler',
            'formatter': 'console_verbose',
            'stream': 'ext://sys.stderr',
        },
        'file': {
            'level': DEFAULT_LEVEL,
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': os.path.expandvars(os.path.expanduser('~/.ansible/ansible-galaxy-cli.log')),
            'formatter': 'file_verbose',
        }
    },

    'loggers': {
        'ansible_galaxy': {
            'handlers': DEFAULT_HANDLERS,
            'level': 'DEBUG',
        },
        'ansible_galaxy.flat_rest_api': {
            'level': 'DEBUG',
        },
        'ansible_galaxy.flat_rest_api.content': {
            'level': 'DEBUG'
        },
        'ansible_galaxy.archive.(extract)': {
            'level': 'INFO',
        },
        'ansible_galaxy_cli': {
            'handlers': DEFAULT_HANDLERS,
            'level': 'DEBUG'
        },
    }
}


def setup(logging_config=None):
    logging_config = logging_config or {}

    conf = logging.config.dictConfig(logging_config)

    # import logging_tree
    # logging_tree.printout()

    return conf


def setup_default():
    return setup(logging_config=DEFAULT_LOGGING_CONFIG)
