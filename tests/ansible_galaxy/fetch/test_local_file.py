import logging
import os
import tarfile
import tempfile


from ansible_galaxy.fetch import local_file
from ansible_galaxy import repository_spec

log = logging.getLogger(__name__)


def test_local_file_fetch(mocker):
    tmp_file_fo = tempfile.NamedTemporaryFile(prefix='tmp', suffix='.tar.gz', delete=False)
    tmp_member_fo = tempfile.NamedTemporaryFile(delete=False, prefix='cccccccccc')
    log.debug('tmp_file_fo.name=%s tmp_file=%s', tmp_file_fo.name, tmp_file_fo)
    tar_file = tarfile.open(mode='w:gz',
                            fileobj=tmp_file_fo)

    pathname = 'MANIFEST.JSON'
    member = tarfile.TarInfo(pathname)
    tar_file.addfile(member, tmp_member_fo)

    tar_file.close()

    repository_spec_ = repository_spec.repository_spec_from_string(tmp_file_fo.name)

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
    assert os.path.isfile(tmp_file_fo.name)

    # results = {'archive_path': '/tmp/tmpcle_fdtp.tar.gz', 'fetch_method': 'local_file',
    # 'custom': {'local_path': '/tmp/tmpcle_fdtp.tar.gz'},
    # 'content': {'galaxy_namespace': None, 'repo_name': '/tmp/tmpcle_fdtp.tar',
    # 'fetched_name': <Mock name='mockRepo.repository_spec.name' id='139946600228288'>}}
    assert results['archive_path'] == tmp_file_fo.name
    assert results['fetch_method'] == 'local_file'
    assert results['custom']['local_path'] == tmp_file_fo.name

    log.debug('should unlink %s here', tmp_file_fo.name)
