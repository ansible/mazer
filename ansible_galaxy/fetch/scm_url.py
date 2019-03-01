import logging

from ansible_galaxy.fetch import base
# mv details of this here
from ansible_galaxy.utils import scm_archive


log = logging.getLogger(__name__)


class ScmUrlFetch(base.BaseFetch):
    fetch_method = 'scm_url'

    def __init__(self, requirement_spec):
        super(ScmUrlFetch, self).__init__()

        self.requirement_spec = requirement_spec

        self.remote_resource = requirement_spec.src

    # scm
    def find(self):
        results = {'content': {'galaxy_namespace': self.requirement_spec.namespace,
                               'repo_name': self.requirement_spec.name},
                   }
        results['custom'] = {'scm_url': self.requirement_spec.src}

        return results

    def fetch(self, find_results=None):
        find_results = find_results or {}
        repository_archive_path = scm_archive.scm_archive_content(src=self.requirement_spec.src,
                                                                  scm=self.requirement_spec.scm,
                                                                  name=self.requirement_spec.name,
                                                                  version=str(self.requirement_spec.version))
        self.local_path = repository_archive_path

        log.debug('repository_archive_path=%s', repository_archive_path)

        results = {'archive_path': repository_archive_path,
                   'download_url': self.requirement_spec.src,
                   'fetch_method': self.fetch_method}
        results['content'] = find_results['content']
        results['custom'] = find_results.get('custom', {})
        results['custom']['scm_url'] = self.requirement_spec.src

        # TODO: what the heck should the version be for a scm_url if one wasnt specified?
        return results
