import logging
import os
import sys

from ansible_galaxy import exceptions
from ansible_galaxy_cli.logger.setup import setup_default
from ansible_galaxy_cli.cli import galaxy
from ansible_galaxy_cli import exceptions as cli_exceptions

log = logging.getLogger(__name__)


def main(args=None):
    setup_default()

    args = args or sys.argv[:]

    # import logging_tree
    # logging_tree.printout()

    log.debug('args: %s', args)
    cli = galaxy.GalaxyCLI(args)
    try:
        cli.parse()
    except cli_exceptions.CliOptionsError as e:
        cli.parser.print_help()
        log.error(e)
        return os.EX_USAGE

    try:
        exit_code = cli.run()
    except exceptions.GalaxyError as e:
        log.exception(e)
        print(e)
        # exit with EX_SOFTWARE on generic error
        exit_code = os.EX_SOFTWARE

    # do any return code setup we need here
    return exit_code
