
import logging
import os

from ansible_galaxy import download

log = logging.getLogger(__name__)


class RemoteUrlFetch(object):
    fetch_method = 'remote_url'

    def __init__(self, remote_url, validate_certs=True):
        self.remote_url = remote_url
        self.local_path = None
        self.validate_certs = validate_certs

    def fetch(self):
        '''Download the remote_url to a temp file

        Can raise GalaxyDownloadError on any exception while downloadin remote_url and saving it.'''

        # NOTE: could move download.fetch_url here instead of splitting it
        content_archive_path = download.fetch_url(self.remote_url, validate_certs=self.validate_certs)
        self.local_path = content_archive_path

        log.debug('content_archive_path=%s', content_archive_path)

        return content_archive_path

    def cleanup(self):
        log.debug("Removing the tmp file %s fetched from remote_url=%s",
                  self.local_path, self.remote_url)
        try:
            os.unlink(self.local_path)
        except (OSError, IOError) as e:
            log.warn('Unable to remove tmp file (%s): %s' % (self.local_path, str(e)))
