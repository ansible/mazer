
import logging

log = logging.getLogger(__name__)


class LocalFileFetch(object):
    fetch_method = 'local_file'

    def __init__(self, repository_spec):
        self.repository_spec = repository_spec
        self.local_path = self.repository_spec.src

    def find(self):
        results = {'content': {'galaxy_namespace': self.repository_spec.namespace,
                               'repo_name': self.repository_spec.name},
                   'specified_content_version': self.repository_spec.version,
                   'specified_repository_spec': self.repository_spec.scm}
        return results

    def fetch(self, find_results=None):
        find_results = find_results or {}

        repository_archive_path = self.local_path

        log.debug('repository_archive_path=%s (inplace)', repository_archive_path)

        results = {'archive_path': repository_archive_path,
                   'fetch_method': self.fetch_method}

        results['custom'] = {'local_path': self.local_path}
        results['content'] = find_results['content']

        return results

    def cleanup(self):
        return None
