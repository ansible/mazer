"""Setup default logging"""

import logging
import logging.config
import os
import yaml

from ansible_galaxy.config import defaults

DEFAULT_CONSOLE_LEVEL = os.getenv('MAZER_LOG_LEVEL', 'WARNING').upper()
DEFAULT_LEVEL = 'DEBUG'

DEFAULT_LOGGING_CONFIG_YAML = os.path.join(os.path.dirname(__file__), 'default-mazer-logging.yml')


FALLBACK_LOGGING_CONFIG = {
    'version': 1,

    'disable_existing_loggers': False,

    'handlers': {
        'null_handler': {
            'class': 'logging.NullHandler',
            'level': 'ERROR',
        },
    },

    'loggers': {
        'ansible_galaxy': {
            'handlers': ['null_handler'],
            'level': 'INFO',
        },
        'ansible_galaxy_cli': {
            'handlers': ['null_handler'],
            'level': 'INFO',
        },
    }
}


class ExpandTildeWatchedFileHandler(logging.handlers.WatchedFileHandler):
    '''A variant of WatchedFileHandler that will expand ~/ in it's filename param'''
    def __init__(self, *args, **kwargs):
        orig_filename = kwargs.pop('filename', '~/.ansible/mazer.log')
        kwargs['filename'] = os.path.expandvars(os.path.expanduser(orig_filename))
        logdir = os.path.dirname(kwargs['filename'])
        if not os.path.exists(logdir):
            os.makedirs(logdir)
        super(ExpandTildeWatchedFileHandler, self).__init__(*args, **kwargs)


def setup(logging_config=None):
    logging_config = logging_config or {}

    logging.config.dictConfig(logging_config)


def load_config_yaml(config_file_path):
    logging_config = None

    try:
        with open(config_file_path, 'r') as logging_config_file:
            logging_config = yaml.safe_load(logging_config_file)
    except (IOError, OSError):
        pass
    except yaml.error.YAMLError as e:
        print(e)

    return logging_config


def setup_default():
    # fallback is basically no setup, null handler, etc
    # builtin, doesn't depend on yaml config
    setup(FALLBACK_LOGGING_CONFIG)

    # load the more extensive defaults from DEFAULT_LOGGING_CONFIG_YAML
    default_logging_config = load_config_yaml(DEFAULT_LOGGING_CONFIG_YAML)
    if default_logging_config:
        setup(default_logging_config)


def setup_custom():
    logging_config = None

    # ~/.ansible/mazer-logging.yml
    LOGGING_CONFIG_YAML = os.path.join(os.path.expanduser(defaults.MAZER_HOME), 'mazer-logging.yml')

    # load custom logging config
    logging_config = load_config_yaml(LOGGING_CONFIG_YAML)

    if logging_config:
        setup(logging_config)
