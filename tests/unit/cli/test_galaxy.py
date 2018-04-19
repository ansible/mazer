
from ansible_galaxy_cli.cli import galaxy


def test_CLI():
    cli = galaxy.GalaxyCLI(args=['info'])
    cli.parse()


def test_run_info():
    cli = galaxy.GalaxyCLI(args=['info'])
    cli.parse()
    cli.run()
