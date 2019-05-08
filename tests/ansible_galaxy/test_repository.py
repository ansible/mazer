import logging
import os

import semantic_version

from ansible_galaxy import repository
from ansible_galaxy import repository_archive
from ansible_galaxy.models.repository import Repository
from ansible_galaxy.models.repository_spec import RepositorySpec
from ansible_galaxy.actions import build
from ansible_galaxy.models.build_context import BuildContext

log = logging.getLogger(__name__)


def display_callback(msg, **kwargs):
    log.debug(msg)


def build_repo_artifact(galaxy_context_, tmp_dir):
    output_path = tmp_dir.mkdir('mazer_test_build_action_test_build')

    collection_path = os.path.join(os.path.dirname(__file__), 'collection_examples/hello')
    build_context = BuildContext(collection_path, output_path=output_path.strpath)
    ret = build._build(galaxy_context_, build_context, display_callback)

    log.debug('ret: %s', ret)

    return ret


def test_load_from_archive_artifact(galaxy_context, tmpdir):
    built_res = build_repo_artifact(galaxy_context, tmpdir)
    archive_path = built_res['build_results'].artifact_file_path

    repo_archive = repository_archive.load_archive(archive_path)
    res = repository.load_from_archive(repo_archive)

    assert isinstance(res, Repository)
    assert isinstance(res.repository_spec, RepositorySpec)
    assert isinstance(res.repository_spec.version, semantic_version.Version)

    assert res.repository_spec.namespace == 'greetings_namespace'
    assert res.repository_spec.name == 'hello'


# def load_from_dir(content_dir, namespace, name, installed=True):
def test_load_from_dir_no_dir():
    res = repository.load_from_dir('/dev/null/doesntexist', 'ns/path', 'some_namespace', 'some_name')

    log.debug('res: %s', res)

    assert res is None, 'load_from_dir() on a dir that does not exist should have returned None'


def test_load_dict():
    data = '''{"foo": "bar"}'''

    res = repository.load(data)

    log.debug('res: %s', res)

    assert isinstance(res, dict)
    assert res['foo'] == 'bar'
