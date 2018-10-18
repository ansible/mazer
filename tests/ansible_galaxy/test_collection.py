import collections
import json
import logging
import os

from ansible_galaxy import repository

log = logging.getLogger(__name__)


def _load_path(file_name):
    # test_data_path = os.path.join(os.path.dirname(__file__), '../../data/%s' % file_name)
    test_data_path = os.path.join(os.path.dirname(__file__), '../data/%s' % file_name)

    log.debug('test_data_path=%s', test_data_path)

    data = open(test_data_path, 'r').read()
    ret = repository.load(data)
    return ret


def test_load_sample():
    ds = _load_path('sample-ansible-galaxy.yml')

    log.debug('ds=%s', json.dumps(ds, indent=4))

    assert isinstance(ds, collections.Mapping)


def test_load_sample2():
    ds = _load_path('sample-ansible-galaxy2.yml')

    log.debug('ds=%s', json.dumps(ds, indent=4))

    assert isinstance(ds, collections.Mapping)
