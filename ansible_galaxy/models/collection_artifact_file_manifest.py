import logging

import attr

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


@attr.s(frozen=True)
class CollectionArtifactFileManifest(object):
    files = attr.ib(factory=list, converter=convert_list_to_artifact_file_list)

    format = attr.ib(default=1,
                     validator=attr.validators.instance_of(int))
