
import logging
import pprint

import yaml

from ansible_galaxy.models.collection_info import \
    CollectionInfo
from ansible_galaxy.models.collection_artifact_file import \
    CollectionArtifactFile
from ansible_galaxy.models.collection_artifact_manifest import \
    CollectionArtifactManifest

log = logging.getLogger(__name__)
pf = pprint.pformat

COLLECTION_MANIFEST_FILENAME = 'MANIFEST.json'


# TODO: replace with a generic version for cases
#       where SomeClass(**dict_from_yaml) works
def load(data_or_file_object):

    # FIXME: This file is json now, so could use the regular json.load()
    #        (this works as well since json is subset of yaml...)
    log.debug('loading collection info from %s',
              pf(data_or_file_object))

    data_dict = yaml.safe_load(data_or_file_object)

    # log.debug('data: %s', pf(data_dict))
    # log.debug('data_dict: %s', data_dict)

    col_info = CollectionInfo(**data_dict['collection_info'])

    file_manifest_file = None
    if data_dict.get('file_manifest_file', None):
        file_manifest_file = CollectionArtifactFile(**data_dict['file_manifest_file'])

    instance = CollectionArtifactManifest(collection_info=col_info,
                                          file_manifest_file=file_manifest_file)

    log.debug('%s instance from_kwargs', type(instance))

    log.debug('collection_artifact_manifest: %r', instance)

    return instance
