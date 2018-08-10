import logging
import os

import attr
import yaml

log = logging.getLogger(__name__)


def load_from_filename(filename, load_method):
    if not os.path.isfile(filename):
        return None

    try:
        f = open(filename, 'r')
        return load_method(f)
    except Exception as e:
        log.exception(e)
        log.debug('Unable to load install info from path: %s', filename)
        return False
    finally:
        f.close()


def save(data, filename):
    log.debug('saving data to %s', filename)
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))

    with open(filename, 'w+') as f:
        # FIXME: just return the install_info dict (or better, build it elsewhere and pass in)
        # FIXME: stop minging self state
        try:
            install_info_ = yaml.safe_dump(attr.asdict(data), f, default_flow_style=False)
        except Exception as e:
            log.warn('unable to serialize data to filename=%s for data=%s', filename, install_info_)
            log.exception(e)
            return False

    log.debug('wrote data to %s', filename)
    return True
