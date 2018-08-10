
import logging
import os

import attr

from ansible_galaxy import collection_info
from ansible_galaxy.models.collection_info import CollectionInfo
from ansible_galaxy import yaml_persist

log = logging.getLogger(__name__)


def test_load():
    file_name = "example_collection_info1.yml"
    test_data_path = os.path.join(os.path.dirname(__file__), '%s' % file_name)
    expected = {'namespace': 'some_namespace',
                'name': 'some_name',
                'version': '11.11.11',
                'author': 'Carlos Boozer',
                'license': 'GPLv2',
                'format_version': 0.0}

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
