import json
import logging
import os
import pprint
import tarfile

import attr
import six

from ansible_galaxy import collection_members
from ansible_galaxy import collection_artifact_manifest
from ansible_galaxy.collection_info import COLLECTION_INFO_FILENAME
from ansible_galaxy.models.collection_artifact_manifest import \
    CollectionArtifactManifest
from ansible_galaxy.utils.text import to_bytes

log = logging.getLogger(__name__)

ARCHIVE_FILENAME_TEMPLATE = 'v{version}.{extension}'
ARCHIVE_FILENAME_EXTENSION = 'tar.gz'

ARCHIVE_TOPDIR_TEMPLATE = '{collection_info.name}-{collection_info.version}'


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


# # MANIFEST BUILDING STAGE
# find collection members in collection_path/  (roles/*, README*, etc)
#   possibly apply 'pre-discover' include/exclude rules here
# filter members / validate members
#   possibly apply 'post-discover' include/exclude rules here
#
# # ARTIFACT CREATION STAGE
# create a artifact manifest (before creating the archive, since the manifest
#                             will be inside the artifact)
#   sort/order?
#   find file chksums here or in the member finding steps? less stuff here...
#
#
# create a artifact file name artifact_file_name=(v$version.tar.gz)
# persist CollectionArtifact as tar.gz to collection_path/release/$artifact_file_name
#
# # POST BUILD / CLEANUP STAGE
# cleanup anything if needed
# display any useful build results info (name and path to artifact, etc)
#
# Build.run() gathers collection_info, the repo/collection members from disk,
#  then creates a ArtifactManifest(collection_info, repo_members)
#  then creates a CollectionArtifact
#  then persists the collection_artifact
#
# CollectionArtifact will have-a Archive/ArchiveBuilder (generic-ish interface to tarfile for ex)
#
# is a CollectionMember/CollectionMembers object needed? CollectionFileWalker?


def filter_artifact_file_name(attr, value):
    '''Used by attr.asdict to remove the src_name attr when serializing'''
    if attr.name == 'src_name':
        return False
    return True


# TODO: this seems like it should use a strategy pattern...
@attr.s
class Build(object):
    build_context = attr.ib()
    collection_info = attr.ib()

    def run(self, display_callback):

        file_walker = collection_members.FileWalker(collection_path=self.build_context.collection_path)
        col_members = collection_members.CollectionMembers(walker=file_walker)

        log.debug('col_members: %s', col_members)
        log.debug('INFO self.collection_info: %s', self.collection_info)

        col_file_names = col_members.run()
        col_files = collection_artifact_manifest.gen_manifest_artifact_files(col_file_names,
                                                                             self.build_context.collection_path)

        manifest = CollectionArtifactManifest(collection_info=self.collection_info,
                                              files=col_files)

        log.debug('manifest: %s', manifest)

        manifest_buf = json.dumps(attr.asdict(manifest,
                                              filter=filter_artifact_file_name),
                                  # sort_keys=True,
                                  indent=4)
        # manifest_buf = yaml.safe_dump(attr.asdict(manifest),
        #                              default_flow_style=False)
        log.debug('manifest buf: %s', manifest_buf)

        # ie, 'v1.2.3.tar.gz', not full path
        archive_filename_basename = \
            ARCHIVE_FILENAME_TEMPLATE.format(version=self.collection_info.version,
                                             extension=ARCHIVE_FILENAME_EXTENSION)

        archive_path = os.path.join(self.build_context.output_path,
                                    archive_filename_basename)
        log.debug('Building archive into archive_path: %s', archive_path)

        # The name of the top level dir in the tar file. It is
        # in the format '{collection_name}-{version}'.
        # NOTE: This doesnt follow convention of 'foo-bar-1.2.3.tar.gz -> foo-bar-1.2.3/*'
        archive_top_dir = ARCHIVE_TOPDIR_TEMPLATE.format(collection_info=self.collection_info)

        log.debug('archive_top_dir: %s', archive_top_dir)

        # 'x:gz' is 'create exclusive gzipped'
        tar_file = tarfile.open(archive_path, mode='w:gz')

        # tar_file.add(archive_top_dir, arcname=archive_top_dir, recursive=False)

        for col_member_file in manifest.files:
            top_dir = False
            # arcname will be a relative path not an abspath at this point
            rel_path = col_member_file.name or col_member_file.src_name
            if rel_path == '.':
                rel_path = ''
            archive_member_path = os.path.join(archive_top_dir, rel_path)

            log.debug('adding %s to %s (from %s)', archive_member_path,
                      archive_path, col_member_file.name)

            log.debug('name=%s, arcname=%s, top_dir=%s', col_member_file.name, archive_member_path, top_dir)

            # if top_dir:
            #     tar_file.add(col_member_file.name, arcname=archive_top_dir, recursive=False)
            # else:
            #     tar_file.add(col_member_file.name, arcname=archive_member_path, recursive=False)
            tar_file.add(col_member_file.src_name, arcname=archive_member_path, recursive=False)

        # add MANIFEST.yml to archive

        b_manifest_buf = to_bytes(manifest_buf)
        b_manifest_buf_bytesio = six.BytesIO(b_manifest_buf)

        archive_manifest_path = os.path.join(archive_top_dir,
                                             collection_artifact_manifest.COLLECTION_MANIFEST_FILENAME)
        log.debug('archive_manifest_path: %s', archive_manifest_path)

        # copy the uid/gid/perms for galaxy.yml to use on the manifest
        # TODO: decide on what the generators owner/group/perms should be (root.root 644?)
        manifest_tar_info = tar_file.gettarinfo(os.path.join(self.build_context.collection_path, COLLECTION_INFO_FILENAME))

        manifest_tar_info.name = archive_manifest_path
        manifest_tar_info.size = len(b_manifest_buf)
        # TODO: set mtime equal to the 'build time' / build_info when we start creating that.

        tar_file.addfile(tarinfo=manifest_tar_info,
                         fileobj=b_manifest_buf_bytesio)

        log.debug('populated tarfile %s: %s', archive_path,
                  pprint.pformat(tar_file.getmembers))

        tar_file.close()

        # could in theory make creating the release artifact work much the same
        # as serializing some object (I mean, that is what it is... but

        messages = ['Building collection: %s' % self.build_context.collection_path,
                    'Created  artifact: %s' % archive_path]

        result = BuildResult(status=BuildStatuses.success,
                             messages=messages,
                             # errors=[],
                             errors=col_members.walker.file_errors,
                             manifest=manifest,
                             artifact_file_path=archive_path)

        for message in result.messages:
            log.info(message)
            display_callback(message)

        for error in result.errors:
            log.error(error)
            display_callback(error, level='warning')

        return result
