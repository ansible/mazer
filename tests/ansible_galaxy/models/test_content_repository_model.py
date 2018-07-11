import logging
import operator

import pytest

from ansible_galaxy.models import content_repository
from ansible_galaxy.models import content_spec

log = logging.getLogger(__name__)


@pytest.fixture
def csf(request):
    _cs = content_spec.ContentSpec(namespace='somenamespace', name='somename', version='1.2.3')
    yield _cs


def test_cr_init_no_args():
    with pytest.raises(TypeError) as exc_info:
        content_repository.ContentRepository()

    log.debug('exc_info.getrepr(): %s', exc_info.getrepr(showlocals=True, style='native'))

    assert exc_info.match("__init__.*missing.*1.*'content_spec'")


def test_cr_init(csf):
    cr = content_repository.ContentRepository(content_spec=csf)

    assert isinstance(cr, content_repository.ContentRepository)
    assert 'ContentRepository' in repr(cr)


def test_icr_init_no_args():
    with pytest.raises(TypeError) as exc_info:
        content_repository.InstalledContentRepository()

    log.debug('exc_info.getrepr(): %s', exc_info.getrepr(showlocals=True, style='native'))

    assert exc_info.match("__init__.*missing.*1.*'content_spec'")


def test_icr_init(csf):
    # cs = content_spec.ContentSpec(namespace='somenamespace', name='somename', version='1.2.3')

    cr = content_repository.InstalledContentRepository(content_spec=csf)

    assert isinstance(cr, content_repository.InstalledContentRepository)
    assert 'ContentRepository' in repr(cr)


def test_icr_init_path(csf):
    path = '/dev/null/wherever'
    cr = content_repository.InstalledContentRepository(content_spec=csf,
                                                       path=path)

    assert isinstance(cr, content_repository.InstalledContentRepository)
    assert path in repr(cr)
    assert cr.path == path


def CR(content_spec=None, path=None):
    if path:
        return content_repository.ContentRepository(content_spec=content_spec, path=path)
    return content_repository.ContentRepository(content_spec=content_spec)


def ICR(content_spec=None, path=None):
    if path:
        return content_repository.InstalledContentRepository(content_spec=content_spec, path=path)
    return content_repository.InstalledContentRepository(content_spec=content_spec)


ns_n = content_spec.ContentSpec(namespace='ns', name='n', version='1.0.0')
diffns_n = content_spec.ContentSpec(namespace='diffns', name='n', version='1.0.0')
ns_n_1_0_0 = ns_n
diffns_n_1_0_0 = diffns_n
ns_n_1_0_1 = content_spec.ContentSpec(namespace='ns', name='n', version='1.0.1')


@pytest.mark.parametrize("left,right,op,expected",
                         [
                             (CR(ns_n), CR(ns_n), operator.eq, True),
                             (CR(ns_n), CR(ns_n), operator.ne, False),
                             (CR(ns_n), CR(ns_n), operator.le, True),
                             (CR(ns_n), CR(ns_n), operator.ge, True),
                             (CR(ns_n), CR(ns_n), operator.is_, False),
                             (CR(ns_n), CR(diffns_n), operator.eq, False),
                             (CR(ns_n), CR(diffns_n), operator.le, False),
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


path1 = '/dev/null/1'
path2 = '/dev/null/2'


@pytest.mark.parametrize("left,right,op,expected",
                         [
                             (ICR(ns_n), ICR(ns_n), operator.eq, True),
                             (ICR(ns_n), ICR(ns_n), operator.ne, False),
                             (ICR(ns_n), ICR(ns_n), operator.le, True),
                             (ICR(ns_n), ICR(ns_n), operator.ge, True),
                             (ICR(ns_n), ICR(ns_n), operator.is_, False),
                             (ICR(ns_n, path=path1), ICR(ns_n, path=path1), operator.eq, True),
                             (ICR(ns_n, path=path1), ICR(ns_n, path=path1), operator.ne, False),
                             (ICR(ns_n, path=path1), ICR(ns_n, path=path2), operator.eq, False),
                             (ICR(ns_n, path=path1), ICR(ns_n, path=path2), operator.ne, True),
                             (ICR(ns_n, path=path1), ICR(ns_n_1_0_1, path=path1), operator.eq, False),
                             (ICR(ns_n, path=path1), ICR(ns_n_1_0_1, path=path1), operator.ne, True),
                             (ICR(ns_n), ICR(ns_n), operator.ne, False),
                             (ICR(ns_n), ICR(ns_n), operator.le, True),
                             (ICR(ns_n), ICR(ns_n), operator.ge, True),
                             (ICR(ns_n), ICR(ns_n), operator.is_, False),
                             # (ICR(ns_n), ICR(diffns_n), operator.eq, False),
                            # (ICR(ns_n), ICR(diffns_n), operator.le, False),
                             #(ICR(ns_n), ICR(diffns_n), operator.ge, False),
                             # (ICR(ns_n), ICR(diffns_n), operator.gt, False),
                             # (ICR(ns_n), ICR(diffns_n), operator.lt, False),

                          ])
def test_icr_equality_ops(left, right, op, expected):
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
