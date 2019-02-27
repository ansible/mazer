

import logging

import attr

from ansible_galaxy.models.collection_info import CollectionInfo

log = logging.getLogger(__name__)


# see https://github.com/ansible/galaxy/issues/957
@attr.s(frozen=True)
class CollectionArtifactManifest(object):
    collection_info = attr.ib(type=CollectionInfo)
    format = attr.ib(default=1)

    # TODO: add a attr with info about the FILES.* file,
    #       files_info_path, files_info_chksum
    #       We need a chksum here, so a signed/verified MANIFEST.json
    #       can be used to verified chksum of FILES.JSON and it can
    #       verify chksums of the rest of the bundled files

    # maybe 'contents' in the future
    #
    # maybe build_info = attr.ib(type=CollectionArtifactBuildInfo)
    #   CollectionArtifactBuildInfo has 'build_date', 'build_tool'
    # created_with =
    # when/build_date =
    # files = []  list of CollectionArtifactManifestFileInfo  (eek... long name)
