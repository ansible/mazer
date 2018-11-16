import logging
import os
import tempfile

from ansible_galaxy.fetch import local_file
from ansible_galaxy import repository_spec

log = logging.getLogger(__name__)


def test_local_file_fetch(mocker):
    tmp_file = tempfile.NamedTemporaryFile(prefix='tmp', suffix='.tar.gz', delete=True)
    log.debug('tmp_file.name=%s tmp_file=%s', tmp_file.name, tmp_file)

    repository_spec_ = repository_spec.repository_spec_from_string(tmp_file.name)

    mocker.patch('ansible_galaxy.fetch.local_file.LocalFileFetch._load_repository_archive',
                 return_value=mocker.Mock(name='mockRepoArchive'))
    mocker.patch('ansible_galaxy.fetch.local_file.LocalFileFetch._load_repository',
                 return_value=mocker.Mock(name='mockRepo'))
    local_fetch = local_file.LocalFileFetch(repository_spec_)

    find_results = local_fetch.find()
    results = local_fetch.fetch(find_results=find_results)

    log.debug('results: %s', results)
    local_fetch.cleanup()

    # LocalFileFetch is acting directly on an existing file, so it's cleanup
    # should _not_ delete the file
    assert os.path.isfile(tmp_file.name)

    # results = {'archive_path': '/tmp/tmpcle_fdtp.tar.gz', 'fetch_method': 'local_file',
    # 'custom': {'local_path': '/tmp/tmpcle_fdtp.tar.gz'},
    # 'content': {'galaxy_namespace': None, 'repo_name': '/tmp/tmpcle_fdtp.tar',
    # 'fetched_name': <Mock name='mockRepo.repository_spec.name' id='139946600228288'>}}
    assert results['archive_path'] == tmp_file.name
    assert results['fetch_method'] == 'local_file'
    assert results['custom']['local_path'] == tmp_file.name
