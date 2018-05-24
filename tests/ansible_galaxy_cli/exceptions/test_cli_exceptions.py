
import logging

import pytest

from ansible_galaxy import exceptions
from ansible_galaxy_cli import exceptions as cli_exceptions

log = logging.getLogger(__name__)


def test_galaxy_cli_error():
    galaxy_cli_error = cli_exceptions.GalaxyCliError()

    assert isinstance(galaxy_cli_error, exceptions.GalaxyError)


# TODO: paramaterize/pytext fixture
def test_galaxy_cli_error_with_message():
    msg = "there was an error in the cli"
    galaxy_cli_error = cli_exceptions.GalaxyCliError(msg)

    assert isinstance(galaxy_cli_error, exceptions.GalaxyError)

    with pytest.raises(cli_exceptions.GalaxyCliError, match=msg) as exc_info:
        raise cli_exceptions.GalaxyCliError(msg)
    log.debug("exc_info: %s", exc_info)


def test_cli_options_error():
    cli_options_error = cli_exceptions.CliOptionsError()

    assert isinstance(cli_options_error, Exception), 'instance of CliOptionsError should be subclass of Exception'
