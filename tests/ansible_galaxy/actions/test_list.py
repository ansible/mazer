import logging
import os

from ansible_galaxy import exceptions
from ansible_galaxy.actions import list as list_action

log = logging.getLogger(__name__)


def display_callback(msg, **kwargs):
    log.debug(msg)


def test_list_empty_roles_paths(galaxy_context):

    # galaxy_context = _galaxy_context(tmpdir)

    try:
        list_action.list(galaxy_context,
                         display_callback=display_callback)
    except exceptions.GalaxyError as e:
        log.debug(e, exc_info=True)
        raise


def test_list_no_content_dir(galaxy_context):
    galaxy_context.content_path = os.path.join(galaxy_context.content_path, 'doesntexist')
    try:
        list_action.list(galaxy_context,
                         display_callback=display_callback)
    except exceptions.GalaxyError as e:
        log.debug(e, exc_info=True)
        return

    assert False, 'Expected a GalaxyError for no dir %s but didnt get one' % galaxy_context.content_path
