import codecs
import json
import logging
import os

from six.moves.urllib.parse import urljoin

from ansible_galaxy import exceptions
from ansible_galaxy import multipart_form
from ansible_galaxy.rest_api import GalaxyAPI
from ansible_galaxy.utils import chksums

log = logging.getLogger(__name__)


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
        'sha256': chksums.sha256sum_from_path(archive_path),
    }

    form = multipart_form.MultiPartForm()
    for key in data:
        form.add_field(key, data[key])

    form.add_file('file',
                  os.path.basename(archive_path),
                  codecs.open(archive_path, 'rb'),
                  'application/octet-stream')

    log.debug('form: %s', form)

    log.debug("Publishing file %s with data: %s" % (archive_path, json.dumps(data)))

    try:
        response_data = api.publish_file(form, publish_api_key)
        log.debug('response_data: %s', response_data)
        results['response_data'] = response_data
    except exceptions.GalaxyError as exc:
        results['success'] = False
        results['errors'].append(str(exc))

    return results


def publish(galaxy_context, archive_path, publish_api_key, display_callback):

    results = _publish(galaxy_context,
                       archive_path,
                       publish_api_key=publish_api_key,
                       display_callback=display_callback)

    log.debug('cli publish action results: %s', results)

    # TODO: add a error_display_callback that understands the format of rest API responses
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
