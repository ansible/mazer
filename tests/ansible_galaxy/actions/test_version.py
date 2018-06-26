import logging

from ansible_galaxy.actions import version

log = logging.getLogger(__name__)


def test_version_data():
    config_path = '/dev/null/some/faux/mazer.yml'
    cli_version = '1.2.3'
    args = ['/bin/mazer', 'version']

    res = version.version_data(config_file_path=config_path,
                               cli_version=cli_version,
                               argv=args)

    log.debug('res: %s', res)

    assert isinstance(res, dict)

    for field in version.VERSION_FIELDS:
        assert field in res

    assert res['config_file'] == config_path
    assert res['version'] == cli_version
    assert res['executable_location'] == args[0]


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


def test_version_repr():
    config_path = '/dev/null/some/faux/mazer.yml'
    cli_version = '1.2.3'
    args = ['/bin/mazer', 'version']

    data = version.version_data(config_file_path=config_path,
                                cli_version=cli_version,
                                argv=args)

    res = version.version_repr(data)
    assert 'mazer.yml' in res


def test_version_repr_empty_data():
    data = {}
    res = version.version_repr(data)

    assert 'name =' in res
    assert 'version =' in res
