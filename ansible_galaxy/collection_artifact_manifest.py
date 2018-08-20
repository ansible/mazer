
import logging
import pprint
import os

import yaml

from ansible_galaxy.utils import chksums
from ansible_galaxy.models.collection_artifact_manifest import \
    CollectionArtifactManifest
from ansible_galaxy.models.collection_artifact_file import \
    CollectionArtifactFile

log = logging.getLogger(__name__)
pf = pprint.pformat

COLLECTION_MANIFEST_FILENAME = "MANIFEST.json"


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


def gen_manifest_artifact_files(file_names, collection_path, chksum_type=None):
    # file_names = file_names or []
    file_names = file_names or []
    default_chksum_type = chksum_type or 'sha256'

    for file_name in file_names:

        current_chksum_type = default_chksum_type

        # TODO: enum
        if os.path.isfile(file_name):
            ftype = 'file'
        if os.path.isdir(file_name):
            ftype = 'dir'

        chksum = None
        if ftype == 'file':
            chksum = chksums.sha256sum_from_path(file_name)
        else:
            chksum = None
            current_chksum_type = None

        dest_relative_path = os.path.relpath(file_name, collection_path)
        arcname = dest_relative_path

        artifact_file = CollectionArtifactFile(src_name=file_name,
                                               # The path where the file will live inside the archive
                                               name=arcname,
                                               ftype=ftype,
                                               chksum_type=current_chksum_type,
                                               chksum_sha256=chksum)

        yield artifact_file
