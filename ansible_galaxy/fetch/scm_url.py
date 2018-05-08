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

    def fetch(self):
        content_archive_path = scm_archive.scm_archive_content(**self.scm_spec)
        self.local_path = content_archive_path

        log.debug('content_archive_path=%s', content_archive_path)

        return content_archive_path
