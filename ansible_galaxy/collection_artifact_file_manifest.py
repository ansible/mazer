import logging
import os
import pprint

import yaml

from ansible_galaxy.utils import chksums
from ansible_galaxy.models.collection_artifact_file import CollectionArtifactFile
from ansible_galaxy.models.collection_artifact_file_manifest import \
    CollectionArtifactFileManifest


pf = pprint.pformat
log = logging.getLogger(__name__)


COLLECTION_FILE_MANIFEST_FILENAME = 'FILES.json'


def load(data_or_file_object):
    # FIXME: This file is json now, so could use the regular json.load()
    #        (this works as well since json is subset of yaml...)
    log.debug('loading collection artifact file manifest from %s',
              pf(data_or_file_object))

    data_dict = yaml.safe_load(data_or_file_object)

    # log.debug('data: %s', pf(data_dict))
    # log.debug('data_dict: %s', data_dict)

    instance = CollectionArtifactFileManifest(**data_dict)

    log.debug('%s instance from_kwargs', type(instance))

    log.debug('collection_file_artifact_manifest: %r', instance)

    return instance


def create_file_manifest_item(file_name, file_name_in_archive):
    if os.path.isfile(file_name):
        # At the moment, 'sha256' is the only supported chksum_type for files
        ftype = 'file'
        chksum_type = 'sha256'
        chksum = chksums.sha256sum_from_path(file_name)

    if os.path.isdir(file_name):
        chksum = None
        chksum_type = None
        ftype = 'dir'

    log.debug('ftype: %s file_name: %s fnia: %s', ftype, file_name, file_name_in_archive)

    artifact_file_item = CollectionArtifactFile(src_name=file_name,
                                                # The path where the file will live inside the archive
                                                name=file_name_in_archive,
                                                ftype=ftype,
                                                chksum_type=chksum_type,
                                                chksum_sha256=chksum)

    return artifact_file_item


def gen_file_manifest_items(file_names, collection_path):
    file_names = file_names or []

    for file_name in file_names:
        file_name_in_archive = os.path.relpath(file_name, collection_path)

        artifact_file_item = create_file_manifest_item(file_name, file_name_in_archive=file_name_in_archive)

        yield artifact_file_item
