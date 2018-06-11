"""Setup default logging"""

import logging
import logging.config
import os

LOG_FILE = os.path.expandvars(os.path.expanduser('~/.ansible/mazer.log')),

DEFAULT_CONSOLE_LEVEL = os.getenv('MAZER_LOG_LEVEL', 'WARNING').upper()
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
        # a plain formatter for messages/errors to stderr
        'console_plain': {
            'format': '%(message)s',
        },
        'file_verbose': {
            'format': '[%(asctime)s %(process)05d %(levelname)-0.1s] %(name)s %(funcName)s:%(lineno)d - %(message)s',
        },
    },

    'filters': {},

    'handlers': {
        'stderr_verbose': {
            'level': DEFAULT_CONSOLE_LEVEL,
            'class': 'logging.StreamHandler',
            'formatter': 'console_verbose',
            'stream': 'ext://sys.stderr',
        },
        'stderr_plain': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'console_plain',
            'stream': 'ext://sys.stderr',
        },
        'file': {
            'level': DEFAULT_LEVEL,
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': os.path.expandvars(os.path.expanduser('~/.ansible/mazer.log')),
            'formatter': 'file_verbose',
        },
        'http_file': {
            'level': DEFAULT_LEVEL,
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': os.path.expandvars(os.path.expanduser('~/.ansible/mazer-http.log')),
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
        'ansible_galaxy.flat_rest_api.api.(http)': {
            'level': 'INFO',
            'handlers': DEFAULT_HANDLERS,
            # to log verbose debug level logging to http_file handler:
            # 'propagate': False,
            # 'level': 'DEBUG',
            # 'handlers': ['http_file'],
        },
        'ansible_galaxy.archive.(extract)': {
            'level': 'INFO',
        },
        'ansible_galaxy_cli': {
            'handlers': DEFAULT_HANDLERS,
            'level': 'DEBUG'
        },
        # For sending messages to stderr and to default handlers
        'ansible_galaxy_cli.(stderr)': {
            'handlers': DEFAULT_HANDLERS + ['stderr_plain'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }
}


def setup(logging_config=None):
    logging_config = logging_config or {}

    conf = logging.config.dictConfig(logging_config)

#    import logging_tree
#    logging_tree.printout()

    return conf


def setup_default():
    return setup(logging_config=DEFAULT_LOGGING_CONFIG)
