import logging

import attr
import pytest

from ansible_galaxy.models import content_spec

log = logging.getLogger(__name__)


def test_init():
    cs = content_spec.ContentSpec(namespace='ns',
                                  name='n',
                                  version='3.4.5')

    assert isinstance(cs, content_spec.ContentSpec)

    log.debug('cs: %s', cs)


def test_frozen():
    cs = content_spec.ContentSpec(namespace='ns',
                                  name='n',
                                  version='3.4.5')

    log.debug('cs: %s', cs)

    with pytest.raises(attr.exceptions.FrozenInstanceError):
        cs.namespace = 'adiffnamespace'

    with pytest.raises(attr.exceptions.FrozenInstanceError):
        cs.name = 'somenewname'

    with pytest.raises(attr.exceptions.FrozenInstanceError):
        cs.version = '0.0.0'

    with pytest.raises(attr.exceptions.FrozenInstanceError):
        cs.src = 'anewsrc'

    with pytest.raises(attr.exceptions.FrozenInstanceError):
        cs.scm = 'anewscm'

    with pytest.raises(attr.exceptions.FrozenInstanceError):
        cs.spec_string = 'not_spec_string'

    with pytest.raises(attr.exceptions.FrozenInstanceError):
        cs.fetch_method = 'not_fetchmethod'


def test_hash():
    cs1 = content_spec.ContentSpec(namespace='cs1',
                                   name='cs1',
                                   version='3.4.5')

    cs1a = content_spec.ContentSpec(namespace='cs1',
                                    name='cs1',
                                    version='3.4.5')

    cs2 = content_spec.ContentSpec(namespace='cs2',
                                   name='c2',
                                   version='3.4.2')

    hash1 = hash(cs1)
    hash1a = hash(cs1a)
    hash2 = hash(cs2)
    log.debug('hash1: %s, hash1a: %s hash2: %s', hash1, hash1a, hash2)

    assert cs1 is not cs2
    assert not cs1 is cs2     # noqa

    data = {}
    data[cs1] = 'c_s_1'
    data[cs2] = 'c_s_2'

    log.debug('data: %s', data)
    assert data[cs1] == 'c_s_1'
    assert data[cs2] == 'c_s_2'

    # cs1a and cs1 have same hash id
    data[cs1a] = 'c_s_1_a'
    assert data[cs1a] == 'c_s_1_a'
    assert data[cs1] == 'c_s_1_a'

    some_set = set([cs1, cs2])
    some_set.add(cs1a)
    log.debug('some_set: %s', some_set)

    assert len(some_set) == 2
    assert cs1 in some_set
    assert cs1a in some_set


def test_equal():
    cs1 = content_spec.ContentSpec(namespace='ns',
                                   name='n',
                                   version='3.4.5')

    cs1a = content_spec.ContentSpec(namespace='ns',
                                    name='n',
                                    version='3.4.5')

    cs2 = content_spec.ContentSpec(namespace='ns2',
                                   name='n2',
                                   version='3.4.2')

    assert cs1 == cs1a
    assert cs1a == cs1

    assert not cs1 != cs1a
    assert not cs1 != cs1a

    assert not cs1 == cs2
    assert not cs2 == cs1

    assert cs1 != cs2
    assert cs2 != cs1

    assert cs1a != cs2
    assert cs2 != cs1a
