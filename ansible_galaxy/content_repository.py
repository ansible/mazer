import logging
import shutil

import yaml

log = logging.getLogger(__name__)

# aka, persistence of ansible_galaxy.models.content_repository


def load(data_or_file_object):
    content_repository = yaml.safe_load(data_or_file_object)
    return content_repository


def remove(installed_repository):
    log.info("Removing installed repository: %s", installed_repository)
    try:
        shutil.rmtree(installed_repository.path)
        return True
    except EnvironmentError as e:
        log.warn('Unable to rm the directory "%s" while removing installed repo "%s": %s',
                 installed_repository.path,
                 installed_repository.label,
                 e)
        log.exception(e)
        raise
