import logging
import os
import sys

from ansible_galaxy import exceptions
from ansible_galaxy_cli.logger.setup import setup_default, setup_custom
from ansible_galaxy_cli.cli import galaxy
from ansible_galaxy_cli import exceptions as cli_exceptions

log = logging.getLogger(__name__)
stderr_log = logging.getLogger('%s.(stderr)' % __package__)


def main(args=None):
    setup_default()
    setup_custom()

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

    # TODO: some level of exception mapper to set exit code based on exception
    try:
        exit_code = cli.run()
    except exceptions.GalaxyConfigFileError as e:
        log.exception(e)

        # The str(e)/error here maybe a multiline yaml error that looks
        # best on a fresh line
        stderr_log.error('Error loading configuration file %s:', e.config_file_path)
        stderr_log.error(e)

        return os.EX_CONFIG
    except exceptions.GalaxyError as e:
        log.exception(e)
        stderr_log.error(e)

        # exit with EX_SOFTWARE on generic error
        exit_code = os.EX_SOFTWARE
    except Exception as e:
        log.exception(e)
        stderr_log.error(e)
        exit_code = os.EX_SOFTWARE

        # let non-Galaxy exceptions bubble up and traceback
        log.debug('Uncaught exception for invocation: %s', cli._orig_args_copy)
        log.error('Uncaught exception, existing with exit code: %s', exit_code)
        raise

    log.debug('exit code: %s', exit_code)
    # do any return code setup we need here
    return exit_code
