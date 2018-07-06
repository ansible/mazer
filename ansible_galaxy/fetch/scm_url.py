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

    def fetch(self):
        content_archive_path = scm_archive.scm_archive_content(src=self.content_spec.src,
                                                               scm=self.content_spec.scm,
                                                               name=self.content_spec.name,
                                                               version=self.content_spec.version)
        self.local_path = content_archive_path

        log.debug('content_archive_path=%s', content_archive_path)

        results = {'archive_path': content_archive_path,
                   'fetch_method': self.fetch_method,
                   'download_url': self.content_spec.src}
        results['custom'] = {'scm_url': self.content_spec.src,
                             'specified_content_spec': self.content_spec.scm}

        # TODO: what the heck should the version be for a scm_url if one wasnt specified?
        return results
