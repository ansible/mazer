
import logging

import attr
import pytest

from ansible_galaxy.models import content

log = logging.getLogger(__name__)


def test_content_type_dir_map():
    assert isinstance(content.CONTENT_TYPE_DIR_MAP, dict)


def test_content_type_dir_map_items():
    for content_type in content.CONTENT_TYPES:
        assert content_type in content.CONTENT_TYPE_DIR_MAP
        if content_type == 'module':
            expected = 'library'
        else:
            expected = '%ss' % content_type
        assert content.CONTENT_TYPE_DIR_MAP[content_type] == expected

    assert 'role' in content.CONTENT_TYPES


def test_galaxy_content_meta_no_args():
    try:
        content.GalaxyContentMeta()
    except TypeError as e:
        log.exception(e)
        return

    assert False, 'GalaxyContentMeta() with no args should raise a TypeError but did not'


def test_galaxy_content_frozen():
    content_meta = content.GalaxyContentMeta(namespace='somenamespace',
                                             name='some_content',
                                             version='1.0.0',
                                             src='some_src',
                                             scm='some_scm',
                                             content_type='role',
                                             content_dir='roles',
                                             path='/dev/null/roles')
    with pytest.raises(attr.exceptions.FrozenInstanceError):
        content_meta.namespace = 'adiffnamespace'

    with pytest.raises(attr.exceptions.FrozenInstanceError):
        content_meta.name = 'somenewname'

    with pytest.raises(attr.exceptions.FrozenInstanceError):
        content_meta.version = '0.0.0'

    with pytest.raises(attr.exceptions.FrozenInstanceError):
        content_meta.src = 'anewsrc'

    with pytest.raises(attr.exceptions.FrozenInstanceError):
        content_meta.scm = 'anewscm'

    with pytest.raises(attr.exceptions.FrozenInstanceError):
        content_meta.content_type = 'notrole'

    with pytest.raises(attr.exceptions.FrozenInstanceError):
        content_meta.content_dir = 'notroles'

    with pytest.raises(attr.exceptions.FrozenInstanceError):
        content_meta.path = '/dev/null/notroles'


def test_galaxy_content_meta():
    content_meta = content.GalaxyContentMeta(namespace='somenamespace',
                                             name='some_content',
                                             version='1.0.0',
                                             src='some_src',
                                             scm='some_scm',
                                             content_type='role',
                                             content_dir='roles',
                                             path='/dev/null/roles')

    assert content_meta.name == 'some_content'
    assert content_meta.content_type == 'role'


def test_galaxy_content_equality():
    content_meta = content.GalaxyContentMeta(namespace='some_namespace',
                                             name='some_content',
                                             version='1.0.0',
                                             content_type='role')

    content_meta_newer = content.GalaxyContentMeta(namespace='some_namespace',
                                                   name='some_content',
                                                   version='2.3.4',
                                                   content_type='role')

    content_meta_newer_dupe = content.GalaxyContentMeta(namespace='some_namespace',
                                                        name='some_content',
                                                        version='2.3.4',
                                                        content_type='role')

    assert content_meta != content_meta_newer
    assert content_meta_newer != content_meta
    assert content_meta_newer == content_meta_newer_dupe
