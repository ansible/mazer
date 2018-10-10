
import logging

import pytest

from ansible_galaxy.models import collection_namespace

log = logging.getLogger(__name__)


def test_collection_namespace_no_namespace():
    with pytest.raises(TypeError, match=r'.*namespace.*'):
        collection_namespace.CollectionNamespace()


def test_collection_namespace_no_path():
    namespace = 'my_namespace'

    cn = collection_namespace.CollectionNamespace(namespace)
    log.debug('cn: %s', cn)

    assert cn.namespace == namespace
    assert cn.path is None


def test_collection_namespace():
    namespace = 'my_namespace'
    path = '/dev/null/path_used_in_test_collection_namespace'

    cn = collection_namespace.CollectionNamespace(namespace, path=path)
    log.debug('cn: %s', cn)

    assert cn.namespace == namespace
    assert cn.path == path
