import logging
import os

from ansible_galaxy import collection_artifact_file_manifest
from ansible_galaxy import yaml_persist
from ansible_galaxy.models.collection_artifact_file import CollectionArtifactFile
from ansible_galaxy.models.collection_artifact_file_manifest import \
    CollectionArtifactFileManifest

log = logging.getLogger(__name__)


def test_load():
    file_name = "example_artifact_file_manifest1.yml"
    test_data_path = os.path.join(os.path.dirname(__file__), '%s' % file_name)

    with open(test_data_path, 'r') as data_fd:
        res = collection_artifact_file_manifest.load(data_fd)
        log.debug('res: %s', res)

        assert isinstance(res, CollectionArtifactFileManifest)
        assert isinstance(res.files, list)
        assert isinstance(res.files[0], CollectionArtifactFile)

        assert res.files[0].name == 'roles/some_role/defaults/main.yml'
        assert res.files[0].ftype == 'file'
        assert res.files[0].chksum_type == 'sha256'
        assert res.files[0].chksum_sha256 == 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'


def test_save(tmpdir):
    temp_dir = tmpdir.mkdir('mazer_collection_archive_file_manifest_unit_test')

    file_name = "example_artifact_file_manifest1.yml"

    temp_file = temp_dir.join(file_name)

    test_data_path = os.path.join(os.path.dirname(__file__), '%s' % file_name)
    with open(test_data_path, 'r') as data_fd:
        res = collection_artifact_file_manifest.load(data_fd)

        log.debug('temp_file.strpath: %s', temp_file.strpath)
        yaml_persist.save(res, temp_file.strpath)

        # open the save()'ed file and load a new collection_artifact_manifest from it
        with open(temp_file.strpath, 'r') as read_fd:
            reloaded = collection_artifact_file_manifest.load(read_fd)

            log.debug('reloaded: %s', reloaded)

            # verify the object loaded from known example matches the example after
            # a save()/load() cycle
            assert reloaded == res

            # read the file again and log the file contents
            read_fd.seek(0)
            buf = read_fd.read()
            log.debug('buf: %s', buf)
