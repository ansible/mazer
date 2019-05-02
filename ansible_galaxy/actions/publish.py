
import hashlib
import json
import logging
import os

from six.moves.urllib.parse import urljoin

from ansible_galaxy import exceptions
from ansible_galaxy.rest_api import GalaxyAPI

log = logging.getLogger(__name__)


def _get_file_checksum(file_path):
    checksum = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            checksum.update(byte_block)
    return checksum.hexdigest()


def _publish(galaxy_context,
             archive_path,
             publish_api_key=None,
             display_callback=None):

    results = {
        'errors': [],
        'success': True
    }

    api = GalaxyAPI(galaxy_context)

    data = {
        'sha256': _get_file_checksum(archive_path),
    }

    log.debug("Publishing file %s with data: %s" % (archive_path, json.dumps(data)))

    try:
        response_data = api.publish_file(data, archive_path, publish_api_key)
        log.debug('response_data: %s', response_data)
        results['response_data'] = response_data
    except exceptions.GalaxyRequestsError as requests_exc:
        results['success'] = False
        results['errors'].append(str(requests_exc))

    return results


def publish(galaxy_context, archive_path, publish_api_key, display_callback):

    results = _publish(galaxy_context,
                       archive_path,
                       publish_api_key=publish_api_key,
                       display_callback=display_callback)

    log.debug('cli publish action results: %s', results)

    if results['errors']:
        for error in results['errors']:
            display_callback(error)

    if results['success']:
        if results['response_data'].get('task', None):
            display_callback('Publish task for %s created at %s' %
                             (archive_path,
                              urljoin(galaxy_context.server['url'],
                                      results['response_data']['task']),
                              ))
        return os.EX_OK  # 0

    return os.EX_SOFTWARE  # 70
