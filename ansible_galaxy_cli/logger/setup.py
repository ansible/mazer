"""Setup default logging"""

import logging
import logging.config
import os

LOG_FILE = os.path.expandvars(os.path.expanduser('~/.ansible/ansible-galaxy-cli.log')),

DEFAULT_LOGGING_CONFIG = {
    'version': 1,

    'disable_existing_loggers': False,

    'formatters': {
        # skip the date for console log handler, but include it for the file log handler
        'console_verbose': {
            'format': '[%(asctime)s,%(msecs)03d %(process)05d %(levelname)-0.1s] %(name)s %(funcName)s:%(lineno)d - %(message)s',
            'datefmt': '%H:%M:%S',
        },
        'file_verbose': {
            'format': '[%(asctime)s %(process)05d %(levelname)-0.1s] %(name)s %(funcName)s:%(lineno)d - %(message)s',
        },
    },

    'filters': {},

    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'console_verbose',
            'stream': 'ext://sys.stderr',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': os.path.expandvars(os.path.expanduser('~/.ansible/ansible-galaxy-cli.log')),
            'formatter': 'file_verbose',
        }
    },

    'loggers': {
        'ansible_galaxy': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        },
        'ansible_galaxy_cli': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        },
    }
}


def setup(logging_config=None):
    logging_config = logging_config or {}

    return logging.config.dictConfig(logging_config)


def setup_default():
    return setup(logging_config=DEFAULT_LOGGING_CONFIG)
