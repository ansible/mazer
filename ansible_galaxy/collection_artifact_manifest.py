
import logging
import pprint

import yaml

from ansible_galaxy.utils import chksums
from ansible_galaxy.models.collection_artifact_manifest import \
    CollectionArtifactManifest
from ansible_galaxy.models.collection_artifact_file import \
    CollectionArtifactFile

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


def collection_manifest_files(file_names=None, chksum_type=None):
    file_names = file_names or []
    chksum_type = chksum_type or 'sha256'

    for file_name in file_names:

        # TODO: figure out the ftype (file/dir/link)
        ftype = 'file'
        chksum = chksums.sha256sum_from_path(file_name)

        artifact_file = CollectionArtifactFile(name=file_name,
                                               ftype=ftype,
                                               chksum_type=chksum_type,
                                               chksum_sha256=chksum)

        yield artifact_file
