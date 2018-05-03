import logging
import os

# mv details of this here
from ansible_galaxy.utils import scm_archive

log = logging.getLogger(__name__)


class ScmUrlFetch(object):
    fetch_method = 'scm_url'

    def __init__(self, scm_url, scm_spec):
        self.scm_url = scm_url
        self.scm_spec = scm_spec
        self.local_path = None

    def fetch(self):
        content_archive_path = scm_archive.scm_archive_content(**self.scm_spec)
        self.local_path = content_archive_path

        log.debug('content_archive_path=%s', content_archive_path)

        return content_archive_path

    def cleanup(self):
        log.debug("Removing the tmp file %s fetched from scm_url=%s",
                  self.local_path, self.scm_url)
        try:
            os.unlink(self.local_path)
        except (OSError, IOError) as e:
            log.warn('Unable to remove tmp file (%s): %s' % (self.local_path, str(e)))
