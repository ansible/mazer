import logging

from ansible_galaxy import exceptions
from ansible_galaxy_cli.logger.setup import setup_default
from ansible_galaxy_cli.cli import galaxy

log = logging.getLogger(__name__)


def main(args=None):
    setup_default()

    args = args or []

    # import logging_tree
    # logging_tree.printout()

    cli = galaxy.GalaxyCLI(args)
    cli.parse()

    try:
        res = cli.run()
    except exceptions.GalaxyError as e:
        log.exception(e)
        print(e)

    # do any return code setup we need here
    return res
