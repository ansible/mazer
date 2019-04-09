import logging
import tempfile

import requests

from ansible_galaxy import exceptions

log = logging.getLogger(__name__)


# FIXME: let the archive_url be passed in
def fetch_url(archive_url, validate_certs=True):
    """
    Downloads the archived content from github to a temp location
    """

    # TODO: should probably be based on/shared with rest API client code, so that
    #       content downloads could support any thing the rest code does
    #       (ie, any TLS cert setup, proxy config, auth options, etc)
    # WHEN: if we change the underlying http client impl at least
    try:
        resp = requests.get(archive_url, verify=validate_certs, stream=True)
        # url_file = open_url(archive_url, validate_certs=validate_certs)

        temp_file = tempfile.NamedTemporaryFile(delete=False,
                                                prefix='tmp-ansible-galaxy-content-archive-',
                                                suffix='.tar.gz')

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
