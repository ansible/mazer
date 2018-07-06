
import logging

log = logging.getLogger(__name__)


class LocalFileFetch(object):
    fetch_method = 'local_file'

    def __init__(self, content_spec):
        self.content_spec = content_spec
        self.local_path = self.content_spec.src

    def find(self):
        results = {'content': {'galaxy_namespace': self.content_spec.namespace,
                               'repo_name': self.content_spec.name},
                   'specified_content_version': self.content_spec.version,
                   'specified_content_spec': self.content_spec.scm}
        return results

    def fetch(self, find_results=None):
        find_results = find_results or {}

        content_archive_path = self.local_path

        log.debug('content_archive_path=%s (inplace)', content_archive_path)

        results = {'archive_path': content_archive_path,
                   'fetch_method': self.fetch_method}

        results['custom'] = {'local_path': self.local_path}
        results['content'] = find_results['content']

        return results

    def cleanup(self):
        return None
