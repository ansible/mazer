import logging

import yaml

from ansible_galaxy import exceptions
from ansible_galaxy.models.collections_lockfile import CollectionsLockfile

log = logging.getLogger(__name__)


# TODO: replace with a generic version for cases
#       where SomeClass(**dict_from_yaml) works
def load(data_or_file_object):
    data_dict = yaml.safe_load(data_or_file_object)

    log.debug('data_dict: %s', data_dict)

    try:
        collections_lockfile = CollectionsLockfile(dependencies=data_dict)
    except ValueError:
        raise
    except Exception as exc:
        log.exception(exc)
        raise exceptions.GalaxyClientError("Error parsing collections lockfile: %s" % str(exc))

    return collections_lockfile
