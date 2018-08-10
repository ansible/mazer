import logging

import attr

log = logging.getLogger(__name__)


# TODO: enum
class BuildStatuses(object):
    success = 'SUCCESS'
    incomplete = 'INCOMPLETE'
    failure = 'FAILURE'


@attr.s
class BuildResult(object):
    status = attr.ib()
    manifest = attr.ib()
    messages = attr.ib(factory=list)
    errors = attr.ib(factory=list)
    artifact_file_path = attr.ib(default=None)


# find the collection_path dir
# read collection_info
# create collection_path/release  (or output_path)
# # MANIFEST BUILDING STAGE
# find collection members in collection_path/  (roles/*, README*, etc)
#   possibly apply 'pre-discover' include/exclude rules here
# filter members / validate members
#   possibly apply 'post-discover' include/exclude rules here
# # ARTIFACT CREATION STAGE
# create a artifact manifest
#   sort/order?
#   find file chksums here or in the member finding steps? less stuff here...
# create a CollectionArtifact.from_manifest(manifest)
#
# create a artifact file name artifact_file_name=($namespace-$name-$version.tar.gz)
# persist CollectionArtifact as tar.gz to collection_path/release/$artifact_file_name
# # POST BUILD / CLEANUP STAGE
# cleanup anything if needed
# display any useful build results info (name and path to artifact, etc)
#
# Build.run() gathers collection_info, the repo/collection members from disk,
#  then creates a ArtifactManifest(collection_info, repo_members)
#  then creates a CollectionArtifact.from_manifest(artifact_manifest)
#  then persists the collection_artifact
#
# CollectionArtifact will have-a Archive/ArchiveBuilder (generic-ish interface to tarfile for ex)
#
# is a CollectionMember/CollectionMembers object needed? CollectionFileWalker?
@attr.s
class Build(object):
    build_context = attr.ib()
    collection_info = attr.ib()

    def run(self, display_callback):
        msg = '* Putting the collection info in stdout, and the manifest in the peanut butter, then shaking it all about'

        result = BuildResult(status=BuildStatuses.incomplete,
                             messages=[msg, "* And thats what it's about"],
                             errors=["XX This didn't actual do anything yet"],
                             manifest=None)

        for message in result.messages:
            log.info(message)
            display_callback(message)

        for error in result.errors:
            log.error(error)
            display_callback(error, level='warning')

        return result
