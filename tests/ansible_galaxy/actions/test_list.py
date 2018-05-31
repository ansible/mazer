import logging
import os
import tempfile

from ansible_galaxy import exceptions
from ansible_galaxy.actions import list as list_action
from ansible_galaxy.models.context import GalaxyContext

log = logging.getLogger(__name__)


def display_callback(msg, **kwargs):
    log.debug(msg)


def _galaxy_context():
    tmp_content_path = tempfile.mkdtemp()
    # FIXME: mock
    server = {'url': 'http://localhost:8000',
              'ignore_certs': False}
    return GalaxyContext(server=server, content_path=tmp_content_path)


def test_list_empty_roles_paths():

    galaxy_context = _galaxy_context()
    role_paths = []
    try:
        list_action.list(galaxy_context,
                         role_paths,
                         display_callback=display_callback)
    except exceptions.GalaxyError as e:
        log.debug(e, exc_info=True)
        raise
        return


def test_list_no_roles_dir():

    galaxy_context = _galaxy_context()
    role_paths = [os.path.join(galaxy_context.content_path, 'roles')]
    try:
        list_action.list(galaxy_context,
                         role_paths,
                         display_callback=display_callback)
    except exceptions.GalaxyError as e:
        log.debug(e, exc_info=True)
        return

    assert False, 'Expected a GalaxyError for no dir %s but didnt get one' % role_paths
    # log.debug('ret: %s', ret)

