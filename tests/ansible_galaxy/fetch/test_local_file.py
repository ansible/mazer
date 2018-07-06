import logging
import os
import tempfile

from ansible_galaxy.fetch import local_file
from ansible_galaxy import content_spec

log = logging.getLogger(__name__)


def test_local_file_fetch():
    tmp_file = tempfile.NamedTemporaryFile(prefix='tmp', delete=True)
    log.debug('tmp_file.name=%s tmp_file=%s', tmp_file.name, tmp_file)

    content_spec_ = content_spec.content_spec_from_string(tmp_file.name)

    local_fetch = local_file.LocalFileFetch(content_spec_)

    find_results = local_fetch.find()
    results = local_fetch.fetch(find_results=find_results)

    log.debug('results: %s', results)
    local_fetch.cleanup()

    # LocalFileFetch is acting directly on an existing file, so it's cleanup
    # should _not_ delete the file
    assert os.path.isfile(tmp_file.name)
