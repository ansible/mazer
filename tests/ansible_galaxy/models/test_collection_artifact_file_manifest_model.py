import logging

import pytest

from ansible_galaxy.models.collection_artifact_file_manifest import CollectionArtifactFileManifest

log = logging.getLogger(__name__)


def test_example():
    files = [{'name': 'roles/some_role/defaults/main.yml',
              'chksum_type': 'sha256',
              'chksum_sha256': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
              'ftype': 'file'}]

    file_manifest = CollectionArtifactFileManifest(files=files)

    log.debug('file_manifest: %s', file_manifest)

    assert isinstance(file_manifest, CollectionArtifactFileManifest)
    assert len(file_manifest.files) == 1


def test_init_no_files():
    files = []
    file_manifest = CollectionArtifactFileManifest(files=files)

    log.debug('file_manifest: %s', file_manifest)

    assert isinstance(file_manifest, CollectionArtifactFileManifest)
    assert len(file_manifest.files) == 0


def test_init_one_empty_file_item():
    files = [{}]

    # Note; KeyError from the converter, not a ValueError from init
    with pytest.raises(KeyError):
        CollectionArtifactFileManifest(files=files)
