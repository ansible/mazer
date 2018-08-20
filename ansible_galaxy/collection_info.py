
import logging
import pprint

import yaml

from ansible_galaxy.models.collection_info import \
    CollectionInfo

log = logging.getLogger(__name__)
pf = pprint.pformat

# DEFAULT_FILENAME = "collection_info.yml"
COLLECTION_INFO_FILENAME = "galaxy.yml"


# TODO: replace with a generic version for cases
#       where SomeClass(**dict_from_yaml) works
def load(data_or_file_object, klass=None):
    log.debug('loading collection info from %s',
              pf(data_or_file_object))

    data_dict = yaml.safe_load(data_or_file_object)

    log.debug('data: %s', pf(data_dict))

    klass = CollectionInfo
    collection_info = CollectionInfo(**data_dict)
    collection_info = klass(**data_dict)

    log.debug('artifact_manifest from_kwargs: %s', collection_info)

    return collection_info
