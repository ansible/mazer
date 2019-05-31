import logging

import pytest

from ansible_galaxy import collection_artifact
from ansible_galaxy import exceptions

log = logging.getLogger(__name__)

EMPTY_SHA = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'


def test_validate_artifact_empty(tmpdir):
    temp_dir = tmpdir.mkdir('mazer_collectio_artifact_unit_test')
    file_name = "example_empty_file"
    temp_file = temp_dir.join(file_name)

    with open(temp_file.strpath, 'w') as tfd:
        tfd.close()

    collection_artifact.validate_artifact(temp_file.strpath, EMPTY_SHA)


def test_validate_artifact_hello_world(tmpdir):
    temp_dir = tmpdir.mkdir('mazer_collectio_artifact_unit_test')
    file_name = "example_empty_file"
    temp_file = temp_dir.join(file_name)

    with open(temp_file.strpath, 'w') as tfd:
        tfd.write('hello world\n')
        tfd.close()

    HELLO_SHA = 'a948904f2f0f479b8f8197694b30184b0d2ed1c1cd2a1ec0fb85d299a192a447'
    collection_artifact.validate_artifact(temp_file.strpath, HELLO_SHA)


def test_validate_artifact_bogus(tmpdir):
    temp_dir = tmpdir.mkdir('mazer_collectio_artifact_unit_test')
    file_name = "example_empty_file"
    temp_file = temp_dir.join(file_name)

    with open(temp_file.strpath, 'w') as tfd:
        tfd.write('hello world\n')
        tfd.close()

    # 'hello' file is not empty of course, so sha check should fail
    with pytest.raises(exceptions.GalaxyArtifactChksumError) as exc_info:
        collection_artifact.validate_artifact(temp_file.strpath, EMPTY_SHA)

    log.debug('exc_info: %s', exc_info)

    exc = exc_info.value

    assert exc.artifact_path == temp_file.strpath
    assert exc.expected == EMPTY_SHA
    assert exc.actual == 'a948904f2f0f479b8f8197694b30184b0d2ed1c1cd2a1ec0fb85d299a192a447'
