
import logging

log = logging.getLogger(__name__)


class LocalFileFetch(object):
    fetch_method = 'local_file'

    def __init__(self, local_path):
        self.local_path = local_path

    def fetch(self):
        content_archive_path = self.local_path

        log.debug('content_archive_path=%s (inplace)', content_archive_path)

        return content_archive_path

    def cleanup(self):
        return None
