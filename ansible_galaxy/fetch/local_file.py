
import logging
import os

from ansible_galaxy import collection_artifact
from ansible_galaxy import repository
from ansible_galaxy import repository_archive

log = logging.getLogger(__name__)


class LocalFileFetch(object):
    fetch_method = 'local_file'

    def __init__(self, requirement_spec):
        self.requirement_spec = requirement_spec
        self.local_path = self.requirement_spec.src

    def find(self):
        vspec = self.requirement_spec.version_spec.specs[0].spec

        results = {'content': {'galaxy_namespace': self.requirement_spec.namespace,
                               'repo_name': self.requirement_spec.name,
                               # For a local file, we created the version_spec to match
                               # exactly the version from the file, so dig into the version_spec
                               # a bit to pull that out.
                               # TODO/FIXME: helper method/wrapper for making this less coupled
                               'version': str(vspec)},
                   'artifact': {'filename': os.path.basename(self.local_path),
                                'size': os.path.getsize(self.local_path)},
                   'custom': {},
                   }
        return results

    def fetch(self, find_results=None):
        find_results = find_results or {}

        repository_archive_path = self.local_path

        log.debug('repository_archive_path=%s (inplace)', repository_archive_path)

        # Note there is currently no chksum validation of local files for most cases
        # since there is no expected chksum
        if find_results.get('artifact', {}).get('sha256', None):
            expected_chksum = find_results['artifact']['sha256']
            collection_artifact.validate_artifact(self.local_path,  expected_chksum)

        repo_archive = self._load_repository_archive(repository_archive_path)

        repo = self._load_repository(repo_archive)

        results = {'archive_path': repository_archive_path,
                   'fetch_method': self.fetch_method}

        results['custom'] = {'local_path': self.local_path}
        results['content'] = find_results['content']
        results['content']['fetched_name'] = repo.repository_spec.name
        # This will have filename, size but usually not sha256
        results['artifact'] = find_results['artifact']

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
