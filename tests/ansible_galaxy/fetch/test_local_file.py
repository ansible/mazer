import logging
import os
import tempfile

from ansible_galaxy.fetch import local_file

log = logging.getLogger(__name__)


def test_local_file_fetch():
    tmp_file = tempfile.NamedTemporaryFile(prefix='tmp', delete=True)
    log.debug('tmp_file.name=%s tmp_file=%s', tmp_file.name, tmp_file)

    local_fetch = local_file.LocalFileFetch(tmp_file.name)
    local_fetch.fetch()

    local_fetch.cleanup()

    # LocalFileFetch is acting directly on an existing file, so it's cleanup
    # should _not_ delete the file
    assert os.path.isfile(tmp_file.name)
