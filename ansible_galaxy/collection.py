import logging
import shutil

import yaml

log = logging.getLogger(__name__)

# aka, persistence of ansible_galaxy.models.collection


def load(data_or_file_object):
    collection = yaml.safe_load(data_or_file_object)
    return collection


def remove(installed_collection):
    log.info("Removing installed collection: %s", installed_collection)
    try:
        shutil.rmtree(installed_collection.path)
        return True
    except EnvironmentError as e:
        log.warn('Unable to rm the directory "%s" while removing installed repo "%s": %s',
                 installed_collection.path,
                 installed_collection.label,
                 e)
        log.exception(e)
        raise
