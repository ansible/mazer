import logging

import pytest

from ansible_galaxy_cli import cli

log = logging.getLogger(__name__)


def test_CLI():
    with pytest.raises(TypeError, match="Can't instantiate abstract class CLI with abstract methods parse"):
        cli.CLI(args=[])
    # log.debug(excinfo.getrepr())
