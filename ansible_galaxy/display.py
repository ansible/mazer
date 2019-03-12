from __future__ import print_function

# if this looks a lot like reimplement 'logging', that is
# true...

import logging
import sys

log = logging.getLogger(__name__)

INFO_LEVEL = {
    'prefix': '',
    'log_level': logging.INFO,
    'stream': sys.stdout,
}

DISPLAY_LEVEL_MAP = {
    'warning': {
        'prefix': 'WARNING| ',
        'log_level': logging.WARNING,
        'stream': sys.stderr
    },
    'info': INFO_LEVEL
}


def stdout_display_callback(*args, **kwargs):
    level_arg = kwargs.get('level', None)
    level_prefix = DISPLAY_LEVEL_MAP.get(level_arg, INFO_LEVEL)['prefix']
    level_stream = DISPLAY_LEVEL_MAP.get(level_arg, INFO_LEVEL)['stream']

    print('%s%s' % (level_prefix, ''.join(args)), file=level_stream)


# will log whatever is display with display callback to the ansible_galaxy.display logger
def log_display_callback(*args, **kwargs):
    level_arg = kwargs.get('level', None)
    # find custom level, otherwise use INFO_LEVELs
    log_level = DISPLAY_LEVEL_MAP.get(level_arg, INFO_LEVEL)['log_level']
    # log.log(log_level, 'DISPLAY: %s', ''.join(args), extra={'display_args': args})
    log.log(log_level, '%s', ''.join(args), extra={'display_args': args})


def display_callback(*args, **kwargs):
    stdout_display_callback(*args, **kwargs)
    log_display_callback(*args, **kwargs)


def null_display_callback(*args, **kwargs):
    pass
