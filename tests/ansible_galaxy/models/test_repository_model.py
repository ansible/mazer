import logging
import operator

import attr
import pytest
import six

from ansible_galaxy.models import repository
from ansible_galaxy.models import repository_spec

log = logging.getLogger(__name__)


@pytest.fixture
def csf(request):
    _cs = repository_spec.RepositorySpec(namespace='somenamespace', name='somename', version='1.2.3')
    yield _cs


def test_frozen(csf):
    cr = repository.Repository(repository_spec=csf)

    new_cr = repository_spec.RepositorySpec(namespace='somenamespace', name='somename', version='1.2.3')

    with pytest.raises(attr.exceptions.FrozenInstanceError):
        cr.repository_spec = new_cr

    with pytest.raises(attr.exceptions.FrozenInstanceError):
        cr.path = '/dev/null/somepath'

    with pytest.raises(attr.exceptions.FrozenInstanceError):
        cr.installed = True


def test_cr_init_no_args():
    with pytest.raises(TypeError) as exc_info:
        repository.Repository()

    log.debug('exc_info.getrepr(): %s', exc_info.getrepr(showlocals=True, style='native'))

    # different TypeError strings for py2 vs py3
    if six.PY3:
        assert exc_info.match("__init__.*missing.*1.*'repository_spec'")

    if six.PY2:
        # __init__() takes at least 2 arguments (1 given)
        assert exc_info.match("__init__.*takes at least.*arguments.*given")


def test_cr_init(csf):
    cr = repository.Repository(repository_spec=csf)

    assert isinstance(cr, repository.Repository)
    assert 'Repository' in repr(cr)


def test_cr_init_path(csf):
    path = '/dev/null/wherever'
    cr = repository.Repository(repository_spec=csf,
                               path=path)

    assert isinstance(cr, repository.Repository)
    assert path in repr(cr)
    assert cr.path == path


def CR(repository_spec=None, path=None):
    if path:
        return repository.Repository(repository_spec=repository_spec, path=path)
    return repository.Repository(repository_spec=repository_spec)


ns_n = repository_spec.RepositorySpec(namespace='ns', name='n', version='1.0.0')
diffns_n = repository_spec.RepositorySpec(namespace='diffns', name='n', version='1.0.0')
ns_n_1_0_0 = ns_n
diffns_n_1_0_0 = diffns_n
ns_n_1_0_1 = repository_spec.RepositorySpec(namespace='ns', name='n', version='1.0.1')


path1 = '/dev/null/1'
path2 = '/dev/null/2'


@pytest.mark.parametrize("left,right,op,expected",
                         [
                             (CR(ns_n), CR(ns_n), operator.eq, True),
                             (CR(ns_n), CR(ns_n), operator.ne, False),
                             (CR(ns_n), CR(ns_n), operator.le, True),
                             (CR(ns_n), CR(ns_n), operator.ge, True),
                             (CR(ns_n), CR(ns_n), operator.is_, False),
                             (CR(ns_n), CR(diffns_n), operator.eq, False),
                             (CR(ns_n), CR(diffns_n), operator.le, False),
                             (CR(ns_n, path=path1), CR(ns_n, path=path1), operator.eq, True),
                             (CR(ns_n, path=path1), CR(ns_n, path=path1), operator.ne, False),
                             (CR(ns_n, path=path1), CR(ns_n, path=path2), operator.eq, False),
                             (CR(ns_n, path=path1), CR(ns_n, path=path2), operator.ne, True),
                             (CR(ns_n, path=path1), CR(ns_n_1_0_1, path=path1), operator.eq, False),
                             (CR(ns_n, path=path1), CR(ns_n_1_0_1, path=path1), operator.ne, True),
                             # (CR(ns_n), CR(diffns_n), operator.ge, False),
                             # (CR(ns_n), CR(diffns_n), operator.gt, False),
                             # (CR(ns_n), CR(diffns_n), operator.lt, False),

                          ])
def test_cr_equality_ops(left, right, op, expected):
    log.debug('left:%s', left)
    log.debug('right: %s', right)
    log.debug('op: %s', op)
    log.debug('expected: %s', expected)
    res = op(left, right)
    log.debug('res: %s', res)
    import pprint
    log.debug('left dict: %s', pprint.pformat(list(left.__attrs_attrs__)))
    assert res == expected


@pytest.mark.parametrize("left,op,expected",
                         [
                             (CR(ns_n), operator.truth, True),
                             (CR(ns_n), operator.not_, False),
                             (CR(ns_n), operator.truth, True),
                             (CR(ns_n), operator.not_, False),
                          ])
def test_cr_bool_ops(left, op, expected):
    log.debug('left: %s, op: %s expected: %s', left, op, expected)
    res = op(left)
    log.debug('res: %s', res)
    assert res == expected
