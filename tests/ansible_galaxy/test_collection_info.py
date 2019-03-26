import attr
import logging
import os
import pytest
import yaml

from ansible_galaxy import collection_info
from ansible_galaxy.models.collection_info import CollectionInfo
from ansible_galaxy import yaml_persist
from ansible_galaxy import exceptions

log = logging.getLogger(__name__)


def test_load():
    file_name = "example_collection_info1.yml"
    test_data_path = os.path.join(os.path.dirname(__file__), '%s' % file_name)
    expected = {'namespace': 'some_namespace',
                'name': 'some_name',
                'version': '11.11.11',
                'authors': ['Carlos Boozer'],
                'description': 'something',
                'license': ['GPL-3.0-or-later'],
                'license_file': None,
                'tags': [],
                'readme': None,
                'documentation': None,
                'homepage': None,
                'issues': None,
                'repository': None,
                'dependencies': {}}

    with open(test_data_path, 'r') as data_fd:
        res = collection_info.load(data_fd)
        log.debug('res: %s', res)

        assert isinstance(res, CollectionInfo)
        res_dict = attr.asdict(res)
        assert res_dict == expected

        for key in res_dict:
            assert getattr(res, key) == res_dict[key] == expected[key]
            assert isinstance(getattr(res, key), type(expected[key]))


def test_save(tmpdir):
    temp_dir = tmpdir.mkdir('mazer_collectio_info_unit_test')

    file_name = "example_collection_info1.yml"

    temp_file = temp_dir.join(file_name)

    test_data_path = os.path.join(os.path.dirname(__file__), '%s' % file_name)
    with open(test_data_path, 'r') as data_fd:
        res = collection_info.load(data_fd)

        log.debug('temp_file.strpath: %s', temp_file.strpath)
        yaml_persist.save(res, temp_file.strpath)

        # open the save()'ed file and load a new collection_artifact_manifest from it
        with open(temp_file.strpath, 'r') as read_fd:
            reloaded = collection_info.load(read_fd)

            log.debug('reloaded: %s', reloaded)

            # verify the object loaded from known example matches the example after
            # a save()/load() cycle
            assert reloaded == res

            # read the file again and log the file contents
            read_fd.seek(0)
            buf = read_fd.read()
            log.debug('buf: %s', buf)


def test_parse_error(tmpdir):
    test_data = {
        'name': 'foo.foo',
        'authors': ['chouseknecht'],
        'license': 'GPL-3.0-or-later',
        'version': '0.0.1',
        'description': 'unit testing thing',
        'foo': 'foo',
    }
    collection_yaml = yaml.safe_dump(test_data, stream=None)
    with pytest.raises(exceptions.GalaxyClientError):
        collection_info.load(collection_yaml)
