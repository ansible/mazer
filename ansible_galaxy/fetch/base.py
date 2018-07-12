import logging
import os

log = logging.getLogger(__name__)


class BaseFetch(object):
    fetch_method = 'base'

    def __init__(self):
        self.local_path = None
        self.cleanup_tmp_files = True

        # remote_resource is whatever was fetched, ie a url or galaxy content spec
        # just an identifier to use in messages
        self.remote_resource = None

    def fetch(self, find_results=None):
        '''Get the content archive, save it to a file locally and return the path to that file'''
        raise NotImplementedError

    def cleanup(self):
        if not self.cleanup_tmp_files:
            log.info("cleanup_tmp_files is false, Not removing the tmp file %s fetched from %s",
                     self.local_path, self.remote_resource)
            return

        log.debug("Removing the tmp file %s fetched from %s",
                  self.local_path, self.remote_resource)

        try:
            os.unlink(self.local_path)
        except (OSError, IOError) as e:
            log.warn('Unable to remove tmp file (%s): %s' % (self.local_path, str(e)))
