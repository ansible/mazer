
import logging

from ansible_galaxy import download
from ansible_galaxy.fetch import base

log = logging.getLogger(__name__)


class RemoteUrlFetch(base.BaseFetch):
    fetch_method = 'remote_url'

    def __init__(self, remote_url, validate_certs=True):
        super(RemoteUrlFetch, self).__init__()

        self.remote_url = remote_url

        self.validate_certs = validate_certs
        log.debug('Validate TLS certificates: %s', self.validate_certs)

        self.remote_resource = remote_url

    def fetch(self):
        '''Download the remote_url to a temp file

        Can raise GalaxyDownloadError on any exception while downloadin remote_url and saving it.'''

        # NOTE: could move download.fetch_url here instead of splitting it
        content_archive_path = download.fetch_url(self.remote_url, validate_certs=self.validate_certs)
        self.local_path = content_archive_path

        log.debug('content_archive_path=%s', content_archive_path)

        results = {'archive_path': content_archive_path,
                   'fetch_method': self.fetch_method}
        results['custom'] = {'remote_url': self.remote_url,
                             'validate_certs': self.validate_certs}
        return content_archive_path
