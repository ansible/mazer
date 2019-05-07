
import datetime
import logging
import os

import semantic_version

from ansible_galaxy import repository_archive
from ansible_galaxy.models.repository_spec import RepositorySpec
from ansible_galaxy.models.install_destination import InstallDestinationInfo
from ansible_galaxy.models.install_info import InstallInfo
from ansible_galaxy.models.installation_results import InstallationResults
from ansible_galaxy.models.collection_artifact_archive import CollectionArtifactArchiveInfo
from ansible_galaxy.models.collection_artifact_archive import CollectionArtifactArchive
from ansible_galaxy.actions import build
from ansible_galaxy.models.build_context import BuildContext

log = logging.getLogger(__name__)


def display_callback(msg, **kwargs):
    log.debug(msg)


def build_repo_artifact(galaxy_context_, tmp_dir):
    output_path = tmp_dir.mkdir('mazer_test_repository_archive_test_build')

    collection_path = os.path.join(os.path.dirname(__file__), 'collection_examples/hello')
    build_context = BuildContext(collection_path, output_path=output_path.strpath)
    ret = build._build(galaxy_context_, build_context, display_callback)

    log.debug('ret: %s', ret)

    return ret


def test_install(galaxy_context, tmpdir):
    built_res = build_repo_artifact(galaxy_context, tmpdir)
    archive_path = built_res['build_results'].artifact_file_path

    repo_archive = repository_archive.load_archive(archive_path)

    log.debug('repo_archive: %s', repo_archive)

    repo_spec = RepositorySpec(namespace='some_namespace',
                               name='some_name',
                               version='1.2.3')

    namespaced_repository_path = '%s/%s' % (repo_spec.namespace,
                                            repo_spec.name)

    destination_info = InstallDestinationInfo(collections_path=galaxy_context.collections_path,
                                              repository_spec=repo_spec,
                                              namespaced_repository_path=namespaced_repository_path,
                                              force_overwrite=True,
                                              editable=False)

    res = repository_archive.install(repo_archive, repo_spec, destination_info, display_callback=display_callback)

    log.debug('res: %s', res)

    assert isinstance(res, InstallationResults)
    assert isinstance(res.install_info, InstallInfo)
    assert isinstance(res.install_info.version, semantic_version.Version)
    assert isinstance(res.installed_datetime, datetime.datetime)


def test_load_from_archive(galaxy_context, tmpdir):
    built_res = build_repo_artifact(galaxy_context, tmpdir)
    archive_path = built_res['build_results'].artifact_file_path

    res = repository_archive.load_archive(archive_path)

    log.debug('res: %s', res)

    assert isinstance(res, CollectionArtifactArchive)
    assert isinstance(res.info, CollectionArtifactArchiveInfo)

    # CollectionRepositoryArtifactArchive(info=RepositoryArchiveInfo(archive_type='multi-content-artifact', top_dir='greetings_namespace.hello-11.11.11'
    assert res.info.archive_type == 'multi-content-artifact'

    assert res.info.top_dir == ''
