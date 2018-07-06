import logging

from ansible_galaxy.fetch import base
# mv details of this here
from ansible_galaxy.utils import scm_archive


log = logging.getLogger(__name__)


class ScmUrlFetch(base.BaseFetch):
    fetch_method = 'scm_url'

    def __init__(self, content_spec):
        super(ScmUrlFetch, self).__init__()

        self.content_spec = content_spec

        self.remote_resource = content_spec.src

    # scm
    def find(self):
        results = {'content': {'galaxy_namespace': self.content_spec.namespace,
                               'repo_name': self.content_spec.name},
                   'specified_content_version': self.content_spec.version,
                   'specified_content_spec': self.content_spec.scm}
        results['custom'] = {'scm_url': self.content_spec.src}

        return results

    def fetch(self, find_results=None):
        find_results = find_results or {}
        content_archive_path = scm_archive.scm_archive_content(src=self.content_spec.src,
                                                               scm=self.content_spec.scm,
                                                               name=self.content_spec.name,
                                                               version=self.content_spec.version)
        self.local_path = content_archive_path

        log.debug('content_archive_path=%s', content_archive_path)

        results = {'archive_path': content_archive_path,
                   'download_url': self.content_spec.src,
                   'fetch_method': self.fetch_method}
        results['content'] = find_results['content']
        results['custom'] = find_results.get('custom', {})
        results['custom']['scm_url'] = self.content_spec.src

        # TODO: what the heck should the version be for a scm_url if one wasnt specified?
        return results
