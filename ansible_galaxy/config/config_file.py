import logging

from ansible_galaxy.config import yaml_file
from ansible_galaxy import exceptions

log = logging.getLogger(__name__)


# TODO: cache?  ideally, should only ever call this once per process
def load(full_file_path):
    try:
        with open(full_file_path, 'r') as config_file_stream:
            return yaml_file.load(config_file_stream)
    except (OSError, IOError) as e:
        log.exception(e)
        log.error('Unable to load config file (%s): %s', e.filename, e)
    except Exception as e:
        log.debug(e, exc_info=True)
        log.error('Unable to load and parse config file (%s): %s', full_file_path, e)
        # TODO: add a py2/py3 compat raise_from method for exception chaining
        raise exceptions.GalaxyConfigFileError(e, config_file_path=full_file_path)

    log.warning('No config data was loaded from file (%s), returning None instead', full_file_path)
    # TODO: empty dict instead?
    return None


def save(config_data, full_file_path):
    try:
        with open(full_file_path, 'w+') as config_file_stream:
            return yaml_file.save(config_data, config_file_stream)
    except Exception as e:
        log.exception(e)
        log.error('Unable to save config file (%s): %s', full_file_path, e)

        # just raise the exception again for now, may want to make this a
        raise
