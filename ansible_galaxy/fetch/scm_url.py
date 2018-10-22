import logging

from ansible_galaxy.fetch import base
# mv details of this here
from ansible_galaxy.utils import scm_archive


log = logging.getLogger(__name__)


class ScmUrlFetch(base.BaseFetch):
    fetch_method = 'scm_url'

    def __init__(self, repository_spec):
        super(ScmUrlFetch, self).__init__()

        self.repository_spec = repository_spec

        self.remote_resource = repository_spec.src

    # scm
    def find(self):
        results = {'content': {'galaxy_namespace': self.repository_spec.namespace,
                               'repo_name': self.repository_spec.name},
                   'specified_content_version': self.repository_spec.version,
                   'specified_repository_spec': self.repository_spec.scm}
        results['custom'] = {'scm_url': self.repository_spec.src}

        return results

    def fetch(self, find_results=None):
        find_results = find_results or {}
        repository_archive_path = scm_archive.scm_archive_content(src=self.repository_spec.src,
                                                                  scm=self.repository_spec.scm,
                                                                  name=self.repository_spec.name,
                                                                  version=self.repository_spec.version)
        self.local_path = repository_archive_path

        log.debug('repository_archive_path=%s', repository_archive_path)

        results = {'archive_path': repository_archive_path,
                   'download_url': self.repository_spec.src,
                   'fetch_method': self.fetch_method}
        results['content'] = find_results['content']
        results['custom'] = find_results.get('custom', {})
        results['custom']['scm_url'] = self.repository_spec.src

        # TODO: what the heck should the version be for a scm_url if one wasnt specified?
        return results
