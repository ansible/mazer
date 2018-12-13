
import logging
import os
import subprocess

import pytest

log = logging.getLogger(__name__)


def popen_git_command(git_command, git_repo_path, expected_return_code=0):
    log.debug('Running command: %s in %s', git_command, git_repo_path)

    try:
        popen = subprocess.Popen(git_command, cwd=git_repo_path.strpath, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as exc:
        log.debug(exc, exc_info=True)
        raise

    stdout, stderr = popen.communicate()
    output = "stdout:\n%s\n\nstderr:\n%s" % (stdout, stderr)

    rc = popen.returncode
    if rc != expected_return_code:
        raise Exception("git command '%s' failed in directory %s (rc=%s, expected_rc=%s)\n%s" %
                        (' '.join(git_command), git_repo_path.strpath, rc, expected_return_code, output))


@pytest.fixture(scope="session")
def tmp_git_repo(tmpdir_factory):
    git_repo_path = tmpdir_factory.mktemp('mazer_unit_test_git_repo')

    git_init_command = ['git', 'init', '.']
    log.debug('Creating tmp git repo in %s', git_repo_path.strpath)

    popen_git_command(git_init_command, git_repo_path)

    git_repo_path.mkdir('some_dir')

    some_file_bases = ['some_dir/another_file', 'some_file', 'README.md', 'build_artifact.pyc']
    some_files = [os.path.join(git_repo_path.strpath, file_base) for file_base in some_file_bases]

    for some_file in some_files:
        with open(some_file, 'w') as somefd:
            somefd.write('whatever\n')

    git_add_command = ['git', 'add', '.']
    popen_git_command(git_add_command, git_repo_path)

    # have to setup git username/email before we can commit. Normally git will try to guess
    # here, based on $HOME, but Since tox envs do not have a $HOME set (or a home dir at all) we get
    # git errors here because of no configured username/name.

    git_email_config_command = ['git', 'config', 'user.email', "mazer_test_user@example.com"]
    popen_git_command(git_email_config_command, git_repo_path)

    git_username_config_command = ['git', 'config', 'user.name', 'Mazer "Corn Dog" Rackham']
    popen_git_command(git_username_config_command, git_repo_path)

    # TODO: setup gitconfig for user.email etc since there is no HOME set in tox envs
    git_commit_command = ['git', 'commit', '--message', 'test commit wip']
    popen_git_command(git_commit_command, git_repo_path)

    return git_repo_path
