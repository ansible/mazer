import logging

import yaml

from ansible_galaxy.models.collection_info import \
    CollectionInfo
from ansible_galaxy import exceptions

log = logging.getLogger(__name__)

COLLECTION_INFO_FILENAME = "galaxy.yml"


# TODO: replace with a generic version for cases
#       where SomeClass(**dict_from_yaml) works
def load(data_or_file_object, klass=None):
    data_dict = yaml.safe_load(data_or_file_object)

    try:
        collection_info = CollectionInfo(**data_dict)
    except ValueError:
        raise
    except Exception as exc:
        raise exceptions.GalaxyClientError("Error parsing collection metadata: %s" % str(exc))

    return collection_info
