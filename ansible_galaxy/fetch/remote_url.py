
import logging

from ansible_galaxy import download
from ansible_galaxy.fetch import base

log = logging.getLogger(__name__)


class RemoteUrlFetch(base.BaseFetch):
    fetch_method = 'remote_url'

    def __init__(self, content_spec, validate_certs=True):
        super(RemoteUrlFetch, self).__init__()

        self.content_spec = content_spec
        self.remote_url = content_spec.src

        self.validate_certs = validate_certs
        log.debug('Validate TLS certificates: %s', self.validate_certs)

        self.remote_resource = self.remote_url

    def find(self):
        results = {'content': {'galaxy_namespace': self.content_spec.namespace,
                               'repo_name': self.content_spec.name},
                   'specified_content_version': self.content_spec.version,
                   'specified_content_spec': self.content_spec.scm}

        return results

    def fetch(self, find_results=None):
        '''Download the remote_url to a temp file

        Can raise GalaxyDownloadError on any exception while downloadin remote_url and saving it.'''

        find_results = find_results or {}

        # NOTE: could move download.fetch_url here instead of splitting it
        content_archive_path = download.fetch_url(self.remote_url, validate_certs=self.validate_certs)
        self.local_path = content_archive_path

        log.debug('content_archive_path=%s', content_archive_path)

        results = {'archive_path': content_archive_path,
                   'fetch_method': self.fetch_method}
        results['content'] = find_results['content']
        results['custom'] = {'remote_url': self.remote_url,
                             'validate_certs': self.validate_certs}
        return results
