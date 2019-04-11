import logging

from ansible_galaxy_cli import main

log = logging.getLogger(__name__)


def test_main_no_args():
    res = main.main(['mazer'])
    log.debug('res: %s', res)


def test_main_list_no_args():
    res = main.main(['mazer', 'list'])
    log.debug('res: %s', res)
