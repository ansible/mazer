import logging
import pytest

from ansible_galaxy.actions import init

log = logging.getLogger(__name__)


def display_callback(msg, **kwargs):
    log.debug(msg)


role_types = \
    [
        'default',
        'apb',
    ]


@pytest.fixture(scope='module',
                params=role_types)
def role_type(request):
    yield request.param


def test_init(tmpdir, role_type):
    role_name = 'test-role'
    init_path = tmpdir.mkdir('init_path')
    role_path = init_path.join(role_name).strpath
    role_skeleton_path = tmpdir.mkdir('role_skeleton').strpath
    skeleton_ignore_expressions = []
    ret = init.init(role_name,
                    init_path,
                    role_path,
                    False,  # force
                    role_skeleton_path,
                    skeleton_ignore_expressions,
                    role_type,
                    display_callback=display_callback)
    assert ret == 0
