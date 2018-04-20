
from ansible_galaxy_cli.cli import galaxy


def main(args=None):
    args = args or []

    cli = galaxy.GalaxyCLI(args)
    cli.parse()

    res = cli.run()

    # do any return code setup we need here
    return res
