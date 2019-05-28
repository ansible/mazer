import logging

import pytest

from ansible_galaxy.models import collections_lockfile

log = logging.getLogger(__name__)


def test_init():
    res = collections_lockfile.CollectionsLockfile()

    assert isinstance(res, collections_lockfile.CollectionsLockfile)
    assert isinstance(res.dependencies, dict)
    assert res.dependencies == {}


def test_init_deps_none():
    res = collections_lockfile.CollectionsLockfile(dependencies=None)

    assert isinstance(res, collections_lockfile.CollectionsLockfile)
    assert isinstance(res.dependencies, dict)
    assert res.dependencies == {}


def test_init_deps_dict():
    not_a_dict = ['foo', 'bar']
    with pytest.raises(TypeError, match='.*dependencies.*') as exc_info:
        collections_lockfile.CollectionsLockfile(dependencies=not_a_dict)

    log.debug('exc_info: %s', exc_info)
