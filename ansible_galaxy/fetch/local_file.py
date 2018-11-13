
import logging

from ansible_galaxy import repository
from ansible_galaxy import repository_archive


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

        repo_archive = self._load_repository_archive(repository_archive_path)

        repo = self._load_repository(repo_archive)

        results = {'archive_path': repository_archive_path,
                   'fetch_method': self.fetch_method}

        results['custom'] = {'local_path': self.local_path}
        results['content'] = find_results['content']
        results['content']['fetched_name'] = repo.repository_spec.name

        return results

    def _load_repository_archive(self, archive_path):
        repo_archive = repository_archive.load_archive(archive_path)
        log.debug('repo_archive: %s', repo_archive)

        return repo_archive

    def _load_repository(self, repository_archive):
        repo = repository.load_from_archive(repository_archive)
        log.debug('repo: %s', repo)
        return repo

    def cleanup(self):
        return None
