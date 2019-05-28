import logging
import os

import pytest

from ansible_galaxy import collections_lockfile
from ansible_galaxy import exceptions
from ansible_galaxy.models.collections_lockfile import CollectionsLockfile

log = logging.getLogger(__name__)


EXAMPLE_LOCKFILE_DIR = os.path.join(os.path.dirname(__file__), '../', 'data', 'collection_lockfiles')


def test_load():
    lockfile_path = os.path.join(EXAMPLE_LOCKFILE_DIR,
                                 'test_1.yml')

    with open(lockfile_path, 'r') as lfd:
        lockfile = collections_lockfile.load(lfd)

        assert isinstance(lockfile, CollectionsLockfile)
        assert 'alikins.collection_inspect' in lockfile.dependencies
        assert 'alikins.collection_ntp' in lockfile.dependencies
        assert lockfile.dependencies['alikins.collection_inspect'] == '>=0.0.1'


def test_load_frozen():
    lockfile_path = os.path.join(EXAMPLE_LOCKFILE_DIR,
                                 'frozen.yml')

    with open(lockfile_path, 'r') as lfd:
        lockfile = collections_lockfile.load(lfd)
        assert isinstance(lockfile, CollectionsLockfile)
        assert 'alikins.collection_inspect' in lockfile.dependencies
        assert 'alikins.collection_ntp' in lockfile.dependencies
        assert lockfile.dependencies['alikins.collection_inspect'] == '==1.0.0'
        assert lockfile.dependencies['alikins.collection_ntp'] == '==2.0.0'


def test_load_floating():
    lockfile_path = os.path.join(EXAMPLE_LOCKFILE_DIR,
                                 'floating.yml')

    with open(lockfile_path, 'r') as lfd:
        lockfile = collections_lockfile.load(lfd)
        assert isinstance(lockfile, CollectionsLockfile)
        assert 'alikins.collection_inspect' in lockfile.dependencies
        assert 'alikins.collection_ntp' in lockfile.dependencies
        assert lockfile.dependencies['alikins.collection_inspect'] == '*'
        assert lockfile.dependencies['alikins.collection_ntp'] == '*'


def test_load_explicit_start():
    lockfile_path = os.path.join(EXAMPLE_LOCKFILE_DIR,
                                 'explicit_start.yml')

    with open(lockfile_path, 'r') as lfd:
        lockfile = collections_lockfile.load(lfd)
        assert isinstance(lockfile, CollectionsLockfile)
        assert 'alikins.collection_inspect' in lockfile.dependencies
        assert 'alikins.collection_ntp' in lockfile.dependencies
        assert lockfile.dependencies['alikins.collection_inspect'] == '*'
        assert lockfile.dependencies['example2.name'] == '>=2.3.4,!=1.0.0'


def test_load_not_dict():
    lockfile_path = os.path.join(EXAMPLE_LOCKFILE_DIR,
                                 'not_dict.yml')

    with open(lockfile_path, 'r') as lfd:
        with pytest.raises(exceptions.GalaxyClientError) as exc_info:
            collections_lockfile.load(lfd)

    log.debug('exc_info: %s', exc_info)
