import logging

from ansible_galaxy_cli.logger import setup

log = logging.getLogger(__name__)


def test_load_config_yaml_no_such_file():
    filename = '/dev/null/doesnotexist.yml'

    res = setup.load_config_yaml(filename)

    # load_config_yaml doesnt throw an exception for missing file
    assert res is None


BAD_YAML = '''
---
stuff: blip
things:
    - notvalidyaml
'''


def test_setup_empty():
    setup.setup({'version': 1})


def test_setup_default(mocker):
    mocker.patch('ansible_galaxy_cli.logger.setup.load_config_yaml',
                 return_value=None)
    setup.setup_default()

    cli_logger = logging.getLogger('ansible_galaxy_cli')

    assert cli_logger.getEffectiveLevel() == logging.INFO

    # should have null handlers at least
    # no hasHandlers for py2.7 so just
    if hasattr(cli_logger, 'hasHandlers'):
        assert cli_logger.hasHandlers()
