import logging
import os
import tarfile
import tempfile


from ansible_galaxy.fetch import local_file
from ansible_galaxy import repository_spec

log = logging.getLogger(__name__)


JSON_DATA = b'''
{
    "collection_info": {
        "namespace": "bcs",
        "name": "bcsping",
        "version": "0.0.1",
        "license": "GPL-2.0-or-later",
        "description": "i blatant copy and rename of the ping module",
        "repository": null,
        "documentation": null,
        "homepage": null,
        "issues": null,
        "authors": [
            "me"
        ],
        "tags": [],
        "readme": "README.md",
        "dependencies": []
    },
    "format": 1,
    "files": [
        {
            "name": ".",
            "ftype": "dir",
            "chksum_type": null,
            "chksum_sha256": null,
            "_format": 1
        },
        {
            "name": "galaxy.yml",
            "ftype": "file",
            "chksum_type": "sha256",
            "chksum_sha256": "728ec435b1717502c305593c7d07116eaacb17ebf714a316f7a925e222f9bb24",
            "_format": 1
        }
    ]
}
'''


def test_local_file_fetch(mocker):
    tmp_file_fo = tempfile.NamedTemporaryFile(prefix='tmp', suffix='.tar.gz', delete=False)
    tmp_member_fo = tempfile.NamedTemporaryFile(delete=False, prefix='cccccccccc')
    log.debug('tmp_file_fo.name=%s tmp_file=%s', tmp_file_fo.name, tmp_file_fo)
    tar_file = tarfile.open(mode='w:gz',
                            fileobj=tmp_file_fo)

    pathname = 'namespace-name-1.2.3/'
    member = tarfile.TarInfo(pathname)
    tar_file.addfile(member, tmp_member_fo)

    new_member = tarfile.TarInfo('namespace-name-1.2.3/MANIFEST.json')
    tmp_member_fo.write(b'%s\n' % JSON_DATA)
    # tmp_member_fo.flush()
    # tmp_member_fo.close()
    tar_file.addfile(new_member, tmp_member_fo)

    log.debug('tar_file members: %s', tar_file.getmembers())
    tar_file.close()
    tmp_file_fo.flush()
    tmp_file_fo.close()

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
