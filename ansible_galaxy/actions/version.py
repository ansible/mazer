import logging
import os
import sys

from ansible_galaxy.utils.text import to_text

log = logging.getLogger(__name__)

VERSION_FIELDS = ('name', 'version', 'config_file', 'uname', 'executable_location', 'python_version', 'python_executable')


def version_data(config_file_path, cli_version, argv):
    data = {}

    data['name'] = 'mazer'
    data['version'] = cli_version
    data['executable_location'] = argv[0]
    data['uname'] = u', '.join(os.uname())

    sys_ver = u"%s" % ''.join(sys.version.splitlines())

    data['python_version'] = sys_ver
    data['python_executable'] = sys.executable

    if config_file_path:
        data['config_file'] = to_text(config_file_path)
    else:
        data['config_file'] = u'No config file found; using defaults'

    return data


def version_repr(version_data):
    lines = []

    for field in VERSION_FIELDS:
        lines.append(u'%s = %s' % (field, version_data.get(field, '')))

    buf = u'\n'.join(lines)
    return buf


def version(config_file_path, cli_version, display_callback=None):
    version_buf = version_repr(version_data(config_file_path, cli_version, sys.argv))
    display_callback(version_buf)
    return 0
