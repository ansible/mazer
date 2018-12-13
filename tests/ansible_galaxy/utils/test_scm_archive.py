import logging

import pytest

from ansible_galaxy import exceptions
from ansible_galaxy.utils import scm_archive


log = logging.getLogger(__name__)

# TODO: Replace cloning from our own local non-bare git repo, with
#       init/populating a test repo in tmp. Ditto for hg.


def test_scm_archive_content_git(tmp_git_repo):
    res = scm_archive.scm_archive_content(src='file://%s' % tmp_git_repo.strpath,
                                          name='mazer_example',
                                          scm='git')

    log.debug('res: %s', res)


def test_scm_archive_content_git_branch_does_not_exist(tmp_git_repo):
    with pytest.raises(exceptions.GalaxyClientError,
                       match=r'- command git checkout .* failed in directory .* \(rc=.*\)') as exc_info:
        scm_archive.scm_archive_content(src='file://%s' % tmp_git_repo.strpath,
                                        name='mazer_example',
                                        scm='git',
                                        version='__branch_name_unlikely_to_exist_w7asyrf7say4fsyrdf__')

    log.debug('exc_info: %s', exc_info)


def test_scm_archive_content_git_scm_src_does_not_exist(tmp_git_repo):
    with pytest.raises(exceptions.GalaxyClientError, match=r'- command .* failed in directory .* \(rc=.*\)') as exc_info:
        scm_archive.scm_archive_content(src='file://%s/__this__should_not_exist__88489er7fw4f__' % tmp_git_repo.strpath,
                                        name='mazer_example',
                                        scm='git')

    # log.debug('res: %s', res)
    log.debug('exc_info: %s', exc_info)
