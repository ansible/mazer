
import logging
import pprint

import yaml

from ansible_galaxy.models.collection_artifact_manifest import \
    CollectionArtifactManifest

log = logging.getLogger(__name__)
pf = pprint.pformat

DEFAULT_FILENAME = "MANIFEST.yml"


# TODO: replace with a generic version for cases
#       where SomeClass(**dict_from_yaml) works
def load(data_or_file_object, klass=None):
    log.debug('loading collection info from %s',
              pf(data_or_file_object))

    data_dict = yaml.safe_load(data_or_file_object)

    log.debug('data: %s', pf(data_dict))

    klass = CollectionArtifactManifest
    instance = klass(**data_dict)

    log.debug('%s instance from_kwargs: %s', type(instance), instance)

    return instance
