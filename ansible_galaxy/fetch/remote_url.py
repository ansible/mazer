
import logging

from ansible_galaxy import download
from ansible_galaxy.fetch import base

log = logging.getLogger(__name__)


class RemoteUrlFetch(base.BaseFetch):
    fetch_method = 'remote_url'

    def __init__(self, requirement_spec, validate_certs=True):
        super(RemoteUrlFetch, self).__init__()

        self.requirement_spec = requirement_spec
        self.remote_url = requirement_spec.src

        self.validate_certs = validate_certs
        log.debug('Validate TLS certificates: %s', self.validate_certs)

        self.remote_resource = self.remote_url

    def find(self):
        results = {'content': {'galaxy_namespace': self.requirement_spec.namespace,
                               'repo_name': self.requirement_spec.name},
                   }

        return results

    def fetch(self, find_results=None):
        '''Download the remote_url to a temp file

        Can raise GalaxyDownloadError on any exception while downloadin remote_url and saving it.'''

        find_results = find_results or {}

        # NOTE: could move download.fetch_url here instead of splitting it
        repository_archive_path = download.fetch_url(self.remote_url, validate_certs=self.validate_certs)
        self.local_path = repository_archive_path

        log.debug('repository_archive_path=%s', repository_archive_path)

        results = {'archive_path': repository_archive_path,
                   'fetch_method': self.fetch_method}
        results['content'] = find_results['content']
        results['custom'] = {'remote_url': self.remote_url,
                             'validate_certs': self.validate_certs}
        return results
