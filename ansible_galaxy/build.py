import logging
import os
import pprint
import tarfile

import attr
import six
import yaml

from ansible_galaxy import collection_members
from ansible_galaxy import collection_artifact_manifest
# from ansible_galaxy.models.collection_artifact import \
#    CollectionArtifact
# from ansible_galaxy.models.collection_artifact_archive import Archive
from ansible_galaxy.models.collection_artifact_manifest import \
    CollectionArtifactManifest
from ansible_galaxy.utils.text import to_bytes

log = logging.getLogger(__name__)

ARCHIVE_FILENAME_TEMPLATE = 'v{version}.{extension}'
ARCHIVE_FILENAME_EXTENSION = 'tar.gz'


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
# create a artifact manifest (before creating the archive, since the manifest
#                             will be inside the artifact)
#   sort/order?
#   find file chksums here or in the member finding steps? less stuff here...
#
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

# TODO: this seems like it should use a strategy pattern...
@attr.s
class Build(object):
    build_context = attr.ib()
    collection_info = attr.ib()

    def run(self, display_callback):
        msg = '* Putting the collection info in stdout, and the manifest in the peanut butter, then shaking it all about'

        file_walker = collection_members.FileWalker(collection_path=self.build_context.collection_path)
        col_members = collection_members.CollectionMembers(walker=file_walker)

        log.debug('col_members: %s', col_members)

        col_file_names = col_members.run()
        col_files = collection_artifact_manifest.collection_manifest_files(col_file_names)

        manifest = CollectionArtifactManifest(collection_info=self.collection_info,
                                              files=col_files)

        log.debug('manifest: %s', manifest)

        manifest_yaml = yaml.safe_dump(attr.asdict(manifest),
                                       default_flow_style=False)
        log.debug('manifest.yml: %s', manifest_yaml)

        # ie, 'v1.2.3.tar.gz', not full path
        archive_filename_basename = \
            ARCHIVE_FILENAME_TEMPLATE.format(version=self.collection_info.version,
                                             extension=ARCHIVE_FILENAME_EXTENSION)

        archive_path = os.path.join(self.build_context.output_path,
                                    archive_filename_basename)

        # archive = Archive.create_from_manifest(manifest, archive_path)
        # tar_file = Archive.create_tarfile(archive_path)
        # 'x:gz' is 'create exclusive gzipped'
        tar_file = tarfile.open(archive_path, mode='w:gz')

        for col_member_file in manifest.files:
            log.debug('adding %s to %s', col_member_file.name, archive_path)

            tar_file.add(col_member_file.name)

        # add MANIFEST.yml to archive

        b_manifest_yaml = to_bytes(manifest_yaml)
        manifest_yaml_bytesio = six.BytesIO(initial_bytes=b_manifest_yaml)
        # manifest_yaml_stringio.write(manifest_yaml)

        manifest_tar_info = tarfile.TarInfo(name='MANIFEST.yml')
        manifest_tar_info.size = len(b_manifest_yaml)

        tar_file.addfile(tarinfo=manifest_tar_info,
                         fileobj=manifest_yaml_bytesio)

        log.debug('populated tarfile %s: %s', archive_path,
                  pprint.pformat(tar_file.getmembers))

        tar_file.close()

        # archive = Archive(payload=tar_file)
        # archive.save()
        # archive = collection_artifact_archive.TarArchive('some_name', tarfile)
        # artifact = CollectionArtifact(manifest=manifest, archive=archive)

        # could in theory make creating the release artifact work much the same
        # as serializing some object (I mean, that is what it is... but

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
