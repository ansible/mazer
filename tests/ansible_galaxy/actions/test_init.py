import logging
import os
import tempfile

from ansible_galaxy.actions import init

log = logging.getLogger(__name__)


def display_callback(msg, **kwargs):
    log.debug(msg)


def test_init(tmpdir):
    role_name = 'test-role'
    # FIXME: needs lots of mocking
    init_path = tmpdir.mkdir('init_path')
    role_path = init_path.join(role_name).strpath
    # role_path = os.path.join(init_path, role_name)
    role_skeleton_path = tmpdir.mkdir('role_skeleton').strpath
    skeleton_ignore_expressions = []
    role_type = 'default'
    ret = init.init(role_name,
                    init_path,
                    role_path,
                    False,  # force
                    role_skeleton_path,
                    skeleton_ignore_expressions,
                    role_type,
                    display_callback=display_callback)

    log.debug('ret: %s', ret)
