

import logging

import attr

from ansible_galaxy.models.collection_info import CollectionInfo
from ansible_galaxy.models.collection_artifact_file import CollectionArtifactFile

log = logging.getLogger(__name__)


def convert_list_to_artifact_file_list(val):
    '''Convert a list of dicts with file info into list of CollectionArtifactFile'''

    new_list = []
    for file_item in val:
        if isinstance(file_item, CollectionArtifactFile):
            new_list.append(file_item)
        else:
            artifact_file = CollectionArtifactFile(name=file_item['name'],
                                                   ftype=file_item['ftype'],
                                                   chksum_type=file_item.get('chksum_type'),
                                                   chksum_sha256=file_item.get('chksum_sha256'))
            new_list.append(artifact_file)

    return new_list


# see https://github.com/ansible/galaxy/issues/957
@attr.s(frozen=True)
class CollectionArtifactManifest(object):
    collection_info = attr.ib(type=CollectionInfo)
    format = attr.ib(default=1)

    files = attr.ib(factory=list, converter=convert_list_to_artifact_file_list)

    # a build_info = attr.ib(type=CollectionArtifactBuildInfo)
    #   CollectionArtifactBuildInfo has 'build_date', 'build_tool'
    # created_with =
    # when/build_date =
    # files = []  list of CollectionArtifactManifestFileInfo  (eek... long name)
