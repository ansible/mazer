import logging
import os
import pprint
import tarfile

from ansible_galaxy import build
from ansible_galaxy.models.build_context import BuildContext
from ansible_galaxy.models.collection_info import CollectionInfo
from ansible_galaxy.models.collection_artifact_manifest import CollectionArtifactManifest


log = logging.getLogger(__name__)
pf = pprint.pformat


def display_callback(*args, **kwargs):
    print(args)


def _build_context(collection_path=None, output_path=None):
    collection_path = collection_path or os.path.join(os.path.dirname(__file__), 'collection_examples/hello')
    log.debug('collection_path: %s', collection_path)
    log.debug('output_path: %s', output_path)

    return BuildContext(collection_path=collection_path,
                        output_path=output_path)


def _collection_info(namespace=None, name=None, version=None, authors=None):
    # name = name or 'some_namespace.some_name'
    namespace = namespace or 'some_namespace'
    name = name or 'some_name'
    version = version or '1.2.3'
    authors = authors or ['Rex Chapman']
    description = "Unit testing thing"
    test_license = 'GPL-3.0-or-later'

    return CollectionInfo(namespace=namespace, name=name, version=version, authors=authors, description=description,
                          license=test_license)


def test_build(tmpdir):
    temp_dir = tmpdir.mkdir('mazer_test_build_unit_test')
    build_context = _build_context(output_path=temp_dir.strpath)
    collection_info = _collection_info()
    build_ = build.Build(build_context, collection_info)

    log.debug('build_: %s', build_)
    assert isinstance(build_, build.Build)
    assert isinstance(build_.build_context, BuildContext)


def test_build_run(tmpdir):
    temp_dir = tmpdir.mkdir('mazer_test_build_run_unit_test')
    build_context = _build_context(output_path=temp_dir.strpath)
    collection_info = _collection_info()
    build_ = build.Build(build_context, collection_info)

    res = build_.run(display_callback)

    assert isinstance(res, build.BuildResult)
    assert isinstance(res.manifest, CollectionArtifactManifest)
    assert isinstance(res.manifest.collection_info, CollectionInfo)
    assert isinstance(res.file_manifest.files, list)

    assert res.manifest.collection_info == collection_info

    for manifest_file in res.file_manifest.files:
        if manifest_file.ftype == 'file':
            assert manifest_file.chksum_type == 'sha256'

    file_names = [x.name for x in res.file_manifest.files if x.ftype == 'file']
    dir_names = [x.name for x in res.file_manifest.files if x.ftype == 'dir']

    log.debug('file_names: %s', file_names)
    log.debug('dir_names: %s', dir_names)

    assert 'roles/some_role/meta/main.yml' in file_names
    assert 'galaxy.yml' in file_names
    assert 'roles' in dir_names
    assert 'roles/some_role/defaults' in dir_names

    assert isinstance(res.messages, list)

    # verify the output file got created
    artifact_file_path = res.artifact_file_path
    assert os.path.isfile(artifact_file_path)
    assert tarfile.is_tarfile(artifact_file_path)

    log.debug('results.errors: %s', res.errors)
