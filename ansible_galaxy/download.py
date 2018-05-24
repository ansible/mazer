import logging
import tempfile

from ansible_galaxy import exceptions
from ansible_galaxy.flat_rest_api.urls import open_url

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
        url_file = open_url(archive_url, validate_certs=validate_certs)

        temp_file = tempfile.NamedTemporaryFile(delete=False,
                                                prefix='tmp-ansible-galaxy-content-archive-',
                                                suffix='.tar.gz')

        data = url_file.read()
        while data:
            temp_file.write(data)
            data = url_file.read()
        temp_file.close()
        return temp_file.name
    except Exception as e:
        # FIXME: there is a ton of reasons a download and save could fail so could likely provided better errors here
        log.exception(e)
        raise exceptions.GalaxyDownloadError(e, url=archive_url)

    return False
