import logging

from ansible_galaxy.fetch import base
# mv details of this here
from ansible_galaxy.utils import scm_archive


log = logging.getLogger(__name__)


class ScmUrlFetch(base.BaseFetch):
    fetch_method = 'scm_url'

    def __init__(self, scm_url, scm_spec):
        super(ScmUrlFetch, self).__init__()

        self.scm_url = scm_url
        self.scm_spec = scm_spec

        self.remote_resource = scm_url

    def fetch(self):
        content_archive_path = scm_archive.scm_archive_content(**self.scm_spec)
        self.local_path = content_archive_path

        log.debug('content_archive_path=%s', content_archive_path)

        results = {'archive_path': content_archive_path,
                   'fetch_method': self.fetch_method,
                   'download_url': self.scm_url}
        results['custom'] = {'scm_url': self.scm_url,
                             'specified_content_spec': self.scm_spec}

        # TODO: what the heck should the version be for a scm_url if one wasnt specified?
        return results
