import logging
import os

from ansible_galaxy import exceptions
from ansible_galaxy.config.defaults import COLLECTIONS_PYTHON_NAMESPACE

log = logging.getLogger(__name__)


class EditableFetch(object):
    fetch_method = 'editable'

    def __init__(self, galaxy_context, requirement_spec):
        self.galaxy_context = galaxy_context
        self.requirement_spec = requirement_spec
        self.local_path = self.requirement_spec.src

    def find(self):
        real_path = os.path.abspath(self.requirement_spec.src)

        log.debug('Searching for a repository to link to as an editable install at %s', real_path)

        if not os.path.isdir(real_path):
            log.warning("%s needs to be a local directory for an editable install" % self.repository.src)
            raise exceptions.GalaxyClientError('Error finding an editable install of %s because %s is not a directory', self.requirement_spec.src, real_path)

        results = {'content': {'galaxy_namespace': self.requirement_spec.namespace,
                               'repo_name': self.requirement_spec.name},
                   'custom': {'real_path': self.requirement_spec.src}
                   }

        return results

    def fetch(self, find_results=None):
        find_results = find_results or {}

        real_path = find_results.get('custom', {}).get('real_path', None)
        if not real_path:
            raise exceptions.GalaxyClientError('Error fetching an editable install of %s because no "real_path" was found in find_results',
                                               self.requirement_spec.src, real_path)

        dst_ns_root = os.path.join(self.galaxy_context.collections_path, COLLECTIONS_PYTHON_NAMESPACE, self.requirement_spec.namespace)

        dst_repo_root = os.path.join(dst_ns_root,
                                     self.requirement_spec.name)

        if not os.path.exists(dst_ns_root):
            os.makedirs(dst_ns_root)

        if not os.path.exists(dst_repo_root):
            os.symlink(real_path, dst_repo_root)

        repository_archive_path = self.local_path

        log.debug('repository_archive_path=%s (inplace) synlink to %s',
                  repository_archive_path,
                  real_path)

        results = {'archive_path': repository_archive_path,
                   'fetch_method': self.fetch_method}

        results['custom'] = {'local_path': self.local_path,
                             'real_path': real_path,
                             'symlinked_repo_root': dst_repo_root}
        results['content'] = find_results['content']

        return results

    def cleanup(self):
        return None
