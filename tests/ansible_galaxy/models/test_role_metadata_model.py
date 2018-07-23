import logging

from ansible_galaxy.models import role_metadata

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
                                         tags=['stuff', 'nginx', 'system', 'devel'])

    log.debug('role_md: %s', role_md)
    assert isinstance(role_md, role_metadata.RoleMetadata)

    assert role_md.name == 'some_role'
    assert role_md.author == 'alikins@redhat.com'
    assert 'stuff' in role_md.tags
    assert isinstance(role_md.tags, list)
    assert role_md.allow_duplicates is False
