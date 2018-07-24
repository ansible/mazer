import logging

from ansible_galaxy.models import role_metadata

import attr

log = logging.getLogger(__name__)


def test_init_empty():
    role_md = role_metadata.RoleMetadata()

    log.debug('role_md: %s', role_md)

    assert isinstance(role_md, role_metadata.RoleMetadata)


def test_basic():
    role_md = role_metadata.RoleMetadata(name='some_role',
                                         author='alikins@redhat.com',
                                         description='some role that does stuff',
                                         company='Red Hat',
                                         license='GPLv3',
                                         galaxy_tags=['stuff', 'nginx', 'system', 'devel'])

    log.debug('role_md: %s', role_md)
    assert isinstance(role_md, role_metadata.RoleMetadata)

    assert role_md.name == 'some_role'
    assert role_md.author == 'alikins@redhat.com'
    assert 'stuff' in role_md.galaxy_tags
    assert isinstance(role_md.galaxy_tags, list)
    assert role_md.allow_duplicates is False


def test_equal():
    role_md1 = role_metadata.RoleMetadata(name='some_role')
    role_md1a = role_metadata.RoleMetadata(name='some_role')
    role_md2 = role_metadata.RoleMetadata(name='a_different_role')

    assert role_md1 == role_md1a
    assert role_md1a == role_md1

    assert not role_md1 == role_md2
    assert not role_md2 == role_md1

    assert role_md1 != role_md2
    assert role_md2 != role_md1


def test_asdict():
    role_md = role_metadata.RoleMetadata(name='some_role',
                                         author='alikins@redhat.com',
                                         description='some role that does stuff',
                                         company='Red Hat',
                                         license='GPLv3',
                                         galaxy_tags=['stuff', 'nginx', 'system', 'devel'])

    log.debug('role_md: %s', role_md)
    role_dict = attr.asdict(role_md)

    assert isinstance(role_dict, dict)
    assert role_dict['name'] == role_md.name == 'some_role'
    assert role_dict['galaxy_tags'] == role_md.galaxy_tags == ['stuff', 'nginx', 'system', 'devel']
