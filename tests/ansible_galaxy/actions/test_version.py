import logging

from ansible_galaxy.actions import version

log = logging.getLogger(__name__)


def test_version():
    config_path = '/dev/null/some/faux/mazer.yml'
    cli_version = '1.2.3'
    # args = ['/bin/mazer', 'version']

    display_items = []

    def callback(*args):
        for arg in args:
            display_items.append(arg)

    res = version.version(config_file_path=config_path,
                          cli_version=cli_version,
                          display_callback=callback)

    assert res == 0

    log.debug('display_items: %s', display_items)

    lines = display_items[0].splitlines()
    assert 'mazer' in lines[0]
