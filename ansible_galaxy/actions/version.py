import logging
import sys

from ansible_galaxy import mazer_version

log = logging.getLogger(__name__)


def version(config_file_path, cli_version, display_callback=None):
    version_buf = mazer_version.version_repr(mazer_version.version_data(config_file_path, cli_version, sys.argv))
    display_callback(version_buf)
    return 0
