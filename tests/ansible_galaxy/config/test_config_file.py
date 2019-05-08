import logging
import tempfile

from ansible_galaxy.config import config_file
from ansible_galaxy.config import config
from ansible_galaxy import exceptions

log = logging.getLogger(__name__)

# Using tempfiles here for tests, can revisit and
# mock out file loading, but yaml_file.py does the
# io/stream object stuff so config_file is mostly dealing
# with file load errors.


def test_load_empty():
    yaml_fo = tempfile.NamedTemporaryFile()

    config_data = config_file.load(yaml_fo.name)

    log.debug('config_data: %s', config_data)
    assert config_data is None


def test_load_bogus_path():
    bogus_path = '/dev/null/doesnt/exist.yml'
    config_data = config_file.load(bogus_path)

    log.debug('config_data: %s', config_data)
    assert config_data is None


BAD_YAML = b'''
---
- foo:
    - just a string
    - ['a', 'json', 'list', 'of', 'strings']
# some garbage
 453 56
 d ddddd
:::-
'''


def test_load_busted_yaml():
    yaml_fo = tempfile.NamedTemporaryFile()
    yaml_fo.write(BAD_YAML)
    yaml_fo.flush()

    try:
        config_data = config_file.load(yaml_fo.name)
    except exceptions.GalaxyConfigFileError as e:
        log.debug(e, exc_info=True)
        return

    log.debug('config_data: %s', config_data)
    assert config_data, 'A GalaxyConfigFileError was expected here'


VALID_YAML = b'''
server:
  ignore_certs: true
  url: https://someserver.example.com
collections_path: ~/.ansible/some_collections_path
global_collections_path: /usr/local/share/collections
options:
  verbosity: 0
version: 1
'''


def test_load_valid_yaml():
    yaml_fo = tempfile.NamedTemporaryFile()
    yaml_fo.write(VALID_YAML)
    yaml_fo.flush()

    config_data = config_file.load(yaml_fo.name)

    log.debug('config_data: %s', config_data)

    assert config_data is not None
    expected_keys = ['server', 'collections_path', 'options']
    for expected_key in expected_keys:
        assert expected_key in config_data

    assert config_data['server']['url'] == 'https://someserver.example.com'
    assert config_data['server']['ignore_certs'] is True
    assert config_data['collections_path'] == '~/.ansible/some_collections_path'
    assert config_data['global_collections_path'] == '/usr/local/share/collections'


def test_save_empty_config():
    yaml_fo = tempfile.NamedTemporaryFile()

    _config = config.Config()

    res = config_file.save(_config.as_dict(), yaml_fo.name)

    log.debug('res: %s', res)


def test_save_config():
    yaml_fo = tempfile.NamedTemporaryFile()

    _config = config.Config()

    config.server = {'url': 'https://someserver.example.com',
                     'ignore_certs': True}
    config.collections_path = '~/.ansible/not-collections-path'

    res = config_file.save(_config.as_dict(), yaml_fo.name)

    log.debug('res: %s', res)


def test_save_bogus_path():
    _config = config.Config()

    config.server = {'url': 'https://someserver.example.com',
                     'ignore_certs': True}
    config.collections_path = '~/.ansible/not-collections-path'

    bogus_path = '/dev/null/doesnt/exist.yml'
    res = None
    try:
        res = config_file.save(_config.as_dict(),
                               bogus_path)
    except (OSError, IOError) as e:
        # at the moment, we expect this to raise an OSError or subclass, to
        # verify assert the filename match
        log.debug(e, exc_info=True)
        assert e.filename == bogus_path
        return

    assert res, 'Expected a OSError, IOError or subclass (NotADirectoryError etc) to be raised here'
