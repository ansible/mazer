import logging

import pytest

from ansible_galaxy_cli.cli import galaxy
from ansible_galaxy_cli import exceptions as cli_exceptions

log = logging.getLogger(__name__)


def test_CLI():
    cli = galaxy.GalaxyCLI(args=['info'])
    cli.parse()
    log.debug('cli.options: %s', cli.options)


def test_run_info():
    cli = galaxy.GalaxyCLI(args=['info'])
    cli.parse()
    with pytest.raises(cli_exceptions.CliOptionsError, match="you must specify a user/role name"):
        cli.run()
