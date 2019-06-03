import logging
import os
import tempfile
import uuid

import requests

from ansible_galaxy import exceptions
from ansible_galaxy import user_agent

log = logging.getLogger(__name__)


def fetch_url(archive_url, validate_certs=True, filename=None, dest_dir=None, chunk_size=None):
    """
    Downloads the archived content from github to a temp location
    """

    request_headers = {}
    request_id = uuid.uuid4().hex
    request_headers['X-Request-ID'] = request_id
    request_headers['User-Agent'] = user_agent.user_agent()

    log.debug('Downloading archive_url: %s', archive_url)

    try:
        resp = requests.get(archive_url, verify=validate_certs,
                            headers=request_headers, stream=True)
    except Exception as e:
        log.exception(e)
        raise exceptions.GalaxyDownloadError(e, url=archive_url)

    # Let tmp filenames begin with the expected artifact filename before '::', except
    # if we don't know it, then it's the UNKNOWN...
    _prefix = filename or 'UNKNOWN-UNKNOWN-UNKNOWN.tar.gz'
    prefix = '%s::' % _prefix

    # TODO: add a configured spool or cache dir and/or default to using
    #       one in MAZER_HOME or maybe ANSIBLE_TMP?
    temp_fd = tempfile.NamedTemporaryFile(delete=False,
                                          suffix='-tmp-mazer-artifact-download',
                                          prefix=prefix)

    try:
        resp.raise_for_status()
    except requests.exceptions.HTTPError as http_exc:
        temp_fd.close()
        os.unlink(temp_fd.name)

        raise exceptions.GalaxyDownloadError(http_exc,
                                             url=http_exc.response.url)

    if resp.history:
        for redirect in resp.history:
            log.debug('Original request for %s redirected. %s is redirected to %s',
                      archive_url, redirect.url, redirect.headers['Location'])

    for chunk in resp.iter_content(chunk_size=chunk_size):
        log.debug('read chunk')
        temp_fd.write(chunk)

    temp_fd.close()

    return temp_fd.name

    return False
