import logging

import pytest

from ansible_galaxy.models import collections_lock

log = logging.getLogger(__name__)


def test_init():
    res = collections_lock.CollectionsLock()

    assert isinstance(res, collections_lock.CollectionsLock)
    assert isinstance(res.dependencies, list)
    assert res.dependencies == []


def test_init_deps_dict():
    not_a_list = {'foo': 'bar'}
    with pytest.raises(TypeError, match='.*dependencies.*') as exc_info:
        collections_lock.CollectionsLock(dependencies=not_a_list)

    log.debug('exc_info: %s', exc_info)
