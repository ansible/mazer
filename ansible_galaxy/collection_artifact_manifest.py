
import logging
import pprint
import os

import yaml

from ansible_galaxy.utils import chksums
from ansible_galaxy.models.collection_info import \
    CollectionInfo
from ansible_galaxy.models.collection_artifact_manifest import \
    CollectionArtifactManifest
from ansible_galaxy.models.collection_artifact_file import \
    CollectionArtifactFile

log = logging.getLogger(__name__)
pf = pprint.pformat

COLLECTION_MANIFEST_FILENAME = 'MANIFEST.json'
COLLECTION_FILE_MANIFEST_FILENAME = 'FILES.json'


# TODO: replace with a generic version for cases
#       where SomeClass(**dict_from_yaml) works
# def load(data_or_file_object, klass=None):
def load(data_or_file_object):

    # FIXME: This file is json now, so could use the regular json.load()
    #        (this works as well since json is subset of yaml...)
    log.debug('loading collection info from %s',
              pf(data_or_file_object))

    data_dict = yaml.safe_load(data_or_file_object)

    # log.debug('data: %s', pf(data_dict))
    # log.debug('data_dict: %s', data_dict)

    col_info = CollectionInfo(**data_dict['collection_info'])
    # klass = CollectionArtifactManifest
    instance = CollectionArtifactManifest(collection_info=col_info,
                                          files=data_dict['files'])
    # instance = klass(**data_dict)

    log.debug('%s instance from_kwargs', type(instance))
    # instance)

    # log.debug('collection_artifact_manifest: %r', instance)

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
