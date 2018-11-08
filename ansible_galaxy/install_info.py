import logging
import os

import yaml

from ansible_galaxy.models.install_info import InstallInfo

log = logging.getLogger(__name__)


def load(data_or_file_object):
    # log.debug('loading content install info from %s', getattr(data_or_file_object, 'name', data_or_file_object))

    info_dict = yaml.safe_load(data_or_file_object)

    # an empty .galaxy_install_info
    if info_dict is None:
        return None

    # log.debug('info_dict: %s', info_dict)
    install_info = InstallInfo(version=info_dict.get('version', None),
                               install_date=info_dict.get('install_date', None),
                               install_date_iso=info_dict.get('install_date_iso', None))

    # log.debug('install_info loaded from %s', install_info)
    return install_info


def load_from_filename(filename):
    if not os.path.isfile(filename):
        return None

    try:
        f = open(filename, 'r')
        return load(f)
    except Exception as e:
        log.exception(e)
        log.debug('Unable to load install info from path: %s', filename)
        return False
    finally:
        f.close()


def save(install_info_dict, filename):
    # log.debug('saving install info to %s', filename)

    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))

    with open(filename, 'w+') as f:
        # FIXME: just return the install_info dict (or better, build it elsewhere and pass in)
        # FIXME: stop minging self state
        try:
            yaml.safe_dump(install_info_dict, f, default_flow_style=False)
        except Exception as e:
            log.warning('unable to serialize .galaxy_install_info to filename=%s for data=%s', filename, install_info_dict)
            log.exception(e)
            return False

    log.debug('wrote galaxy_install_info to %s', filename)
    return True
