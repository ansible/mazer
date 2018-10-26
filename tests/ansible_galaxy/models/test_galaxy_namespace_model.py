
import logging

import pytest
import six

from ansible_galaxy.models import galaxy_namespace

log = logging.getLogger(__name__)


def test_galaxy_namespace_no_namespace():
    with pytest.raises(TypeError) as exc_info:
        galaxy_namespace.GalaxyNamespace()

    # different TypeError strings for py2 vs py3
    log.debug('exc_info.getrepr(): %s', exc_info.getrepr(showlocals=True, style='native'))

    if six.PY3:
        # example: TypeError: __init__() missing 1 required positional argument: 'namespace'
        assert exc_info.match("__init__.*missing.*1.*'namespace'")

    if six.PY2:
        # TypeError: __init__() takes at least 2 arguments (1 given)
        assert exc_info.match("__init__.*takes at least.*arguments.*given")


def test_galaxy_namespace_no_path():
    namespace = 'my_namespace'

    gn = galaxy_namespace.GalaxyNamespace(namespace)
    log.debug('gn: %s', gn)

    assert gn.namespace == namespace
    assert gn.path is None


def test_galaxy_namespace():
    namespace = 'my_namespace'
    path = '/dev/null/path_used_in_test_collection_namespace'

    gn = galaxy_namespace.GalaxyNamespace(namespace, path=path)
    log.debug('gn: %s', gn)

    assert gn.namespace == namespace
    assert gn.path == path
