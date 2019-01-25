
import attr
import hashlib
import json
import logging
import os
import tarfile

from ansible_galaxy.rest_api import GalaxyAPI
from ansible_galaxy import collection_artifact_manifest
from ansible_galaxy import exceptions

log = logging.getLogger(__name__)


def _get_file_checksum(file_path):
    checksum = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            checksum.update(byte_block)
    return checksum.hexdigest()


def _publish(galaxy_context,
             archive_path,
             display_callback=None):

    results = {
        'errors': [],
        'success': True
    }

    archive = tarfile.open(archive_path, 'r')
    top_dir = os.path.commonprefix(archive.getnames())
    manifest_path = os.path.join(top_dir,
                                 collection_artifact_manifest.COLLECTION_MANIFEST_FILENAME)
    try:
        manifest_file = archive.extractfile(manifest_path)
    except tarfile.TarError as exc:
        raise exceptions.GalaxyPublishError(str(exc), archive_path=archive_path)

    try:
        manifest = collection_artifact_manifest.load(manifest_file)
    except Exception as exc:
        raise exceptions.GalaxyPublishError(str(exc), archive_path=archive_path)

    display_callback(json.dumps(attr.asdict(manifest.collection_info)))

    api = GalaxyAPI(galaxy_context)

    collection_name = manifest.collection_info.name
    namespace_name = manifest.collection_info.namespace

    log.debug("Attempting to fetch Galaxy namespace %s" % namespace_name)
    namespace = api.fetch_namespace(namespace_name)

    namespace_id = namespace.get('id')
    data = {
        'sha256': _get_file_checksum(archive_path),
        'name': collection_name,
        'version': manifest.collection_info.version
    }
    log.debug("Publishing file %s with data: %s" % (archive_path, json.dumps(data)))
    api.publish_file(namespace_id, data, archive_path)
    return results


def publish(galaxy_context, archive_path, display_callback):

    results = _publish(galaxy_context,
                       archive_path,
                       display_callback=display_callback)

    log.debug('cli publish action results: %s', json.dumps(results))

    if results['errors']:
        for error in results['errors']:
            display_callback(error)

    if results['success']:
        return os.EX_OK  # 0

    return os.EX_SOFTWARE  # 70
