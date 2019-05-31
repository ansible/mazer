import logging
import tempfile
import uuid

import requests

from ansible_galaxy import exceptions
from ansible_galaxy import user_agent

log = logging.getLogger(__name__)


def fetch_url(archive_url, validate_certs=True, filename=None):
    """
    Downloads the archived content from github to a temp location
    """

    request_headers = {}
    request_id = uuid.uuid4().hex
    request_headers['X-Request-ID'] = request_id
    request_headers['User-Agent'] = user_agent.user_agent()

    try:
        log.debug('Downloading archive_url: %s', archive_url)
        resp = requests.get(archive_url, verify=validate_certs,
                            headers=request_headers, stream=True)

        # so tmp filenames begin with the expected artifact filename before '::', except
        # if we don't know it, then it's the UNKNOWN...
        _prefix = filename or 'UNKNOWN-UNKNOWN-UNKNOWN.tar.gz'
        prefix = '%s::' % _prefix

        # TODO: add a configured spool or cache dir and/or default to using
        #       one in MAZER_HOME or maybe ANSIBLE_TMP?
        temp_file = tempfile.NamedTemporaryFile(delete=False,
                                                suffix='-tmp-mazer-artifact-download',
                                                prefix=prefix)

        if resp.history:
            for redirect in resp.history:
                log.debug('Original request for %s redirected. %s is redirected to %s',
                          archive_url, redirect.url, redirect.headers['Location'])

        # TODO: test for short reads
        for chunk in resp.iter_content(chunk_size=None):
            temp_file.write(chunk)

        temp_file.close()

        return temp_file.name
    except Exception as e:
        # FIXME: there is a ton of reasons a download and save could fail so could likely provided better errors here
        log.exception(e)
        raise exceptions.GalaxyDownloadError(e, url=archive_url)

    return False
