
import logging

from ansible_galaxy import mazer_version

log = logging.getLogger(__name__)


def test_version_data():
    config_path = '/dev/null/some/faux/mazer.yml'
    cli_version = '1.2.3'
    args = ['/bin/mazer', 'version']

    res = mazer_version.version_data(config_file_path=config_path,
                                     cli_version=cli_version,
                                     argv=args)

    log.debug('res: %s', res)

    assert isinstance(res, dict)

    for field in mazer_version.VERSION_FIELDS:
        assert field in res

    assert res['config_file'] == config_path
    assert res['version'] == cli_version
    assert res['executable_location'] == args[0]


def test_version_repr():
    config_path = '/dev/null/some/faux/mazer.yml'
    cli_version = '1.2.3'
    args = ['/bin/mazer', 'version']

    data = mazer_version.version_data(config_file_path=config_path,
                                      cli_version=cli_version,
                                      argv=args)

    res = mazer_version.version_repr(data)
    assert 'mazer.yml' in res


def test_version_repr_empty_data():
    data = {}
    res = mazer_version.version_repr(data)

    assert 'name =' in res
    assert 'version =' in res
