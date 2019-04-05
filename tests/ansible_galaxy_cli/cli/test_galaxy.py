import logging
import os
import tarfile

import pytest

from ansible_galaxy_cli.cli import galaxy
from ansible_galaxy_cli import exceptions as cli_exceptions

log = logging.getLogger(__name__)

COLLECTION_INFO1 = '''
namespace: some_namespace
name: some_namespace
version: 3.1.4
license:
 - GPL-3.0-or-later
description: 'a thing'
authors:
    - Adrian Likins
'''


def test_build_no_args(mazer_args_for_test):
    cli = galaxy.GalaxyCLI(args=mazer_args_for_test + ['build'])
    cli.parse()

    log.debug('cli.options: %s', cli.options)
    assert cli.options.output_path is None
    assert cli.options.collection_path is None
    assert cli.args == []


# def test_build_run_no_args():
#     cli = galaxy.GalaxyCLI(args=['mazer', 'build', 'fooo'])
#     cli.parse()
#     log.debug('cli.options: %s', cli.options)

#     rc = cli.run()

#     assert rc == os.EX_SOFTWARE


def test_build_run_tmp_collection_path(tmpdir, mazer_args_for_test):
    temp_dir = tmpdir.mkdir('mazer_cli_built_run_tmp_output_path_unit_test')
    log.debug('temp_dir: %s', temp_dir.strpath)

    collection_path = tmpdir.mkdir('collection').strpath
    output_path = tmpdir.mkdir('output').strpath

    info_path = os.path.join(collection_path, 'galaxy.yml')
    info_fd = open(info_path, 'w')
    info_fd.write(COLLECTION_INFO1)
    info_fd.close()

    cli = galaxy.GalaxyCLI(args=mazer_args_for_test +
                           ['build', '--collection-path', collection_path,
                            '--output-path', output_path])
    cli.parse()

    log.debug('cli.options: %s', cli.options)

    res = cli.run()
    log.debug('res: %s', res)

    assert os.path.isdir(output_path)

    expected_artifact_path = os.path.join(output_path, 'some_namespace-some_namespace-3.1.4.tar.gz')

    assert os.path.isfile(expected_artifact_path)
    assert tarfile.is_tarfile(expected_artifact_path)


def test_info(mazer_args_for_test):
    cli = galaxy.GalaxyCLI(args=mazer_args_for_test + ['info'])
    cli.parse()

    log.debug('cli.options: %s', cli.options)


def test_run_info(mazer_args_for_test):
    cli = galaxy.GalaxyCLI(args=mazer_args_for_test + ['info'])
    cli.parse()
    with pytest.raises(cli_exceptions.CliOptionsError, match="you must specify a collection name"):
        cli.run()


def test_run_list(mazer_args_for_test):
    cli = galaxy.GalaxyCLI(args=mazer_args_for_test + ['list'])
    cli.parse()
    res = cli.run()

    log.debug('mat: %s', mazer_args_for_test)
    log.debug('res: %s', res)


def test_publish_no_args(mazer_args_for_test):
    cli = galaxy.GalaxyCLI(args=mazer_args_for_test + ['publish'])
    cli.parse()
    with pytest.raises(cli_exceptions.CliOptionsError, match="you must specify a path"):
        cli.run()
