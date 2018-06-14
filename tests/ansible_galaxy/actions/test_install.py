
import logging
import mock
import tempfile

from ansible_galaxy.actions import install
from ansible_galaxy import exceptions
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


def test_install_contents_empty_contents(galaxy_context):
    contents = []

    ret = install.install_contents(galaxy_context,
                                   requested_contents=contents,
                                   install_content_type='role',
                                   display_callback=display_callback)

    log.debug('ret: %s', ret)
    assert ret == 0


def test_install_contents(galaxy_context):
    contents = [mock.Mock(content_type='role',
                          # FIXME: install bases update on install_info existing, so will fail for other content
                          install_info=None,
                          metadata={'content_type': 'role'})]

    ret = install.install_contents(galaxy_context,
                                   requested_contents=contents,
                                   install_content_type='role',
                                   display_callback=display_callback)

    log.debug('ret: %s', ret)
    assert ret == 0


def test_install_contents_module(galaxy_context):
    contents = [mock.Mock(content_type='module',
                          # FIXME: install bases update on install_info existing, so will fail for other content
                          install_info=None,
                          metadata={'content_type': 'module'})]

    ret = install.install_contents(galaxy_context,
                                   requested_contents=contents,
                                   install_content_type='module',
                                   display_callback=display_callback)

    log.debug('ret: %s', ret)
    # assert ret == 0


def test_build_content_set_empty(galaxy_context):
    ret = install._build_content_set([], 'role', galaxy_context)
    log.debug('ret: %s', ret)
    assert ret == []


# even though 'blrp' isnt a valid spec, _build_content_set return something for now
def test_build_content_set_malformed(galaxy_context):
    content_spec = 'no_namespace_here'
    try:
        install._build_content_set([content_spec], 'role', galaxy_context)
    except exceptions.GalaxyError as e:
        log.exception(e)
        return

    assert False, 'Expected a GalaxyError to be raised here since the content_spec %s has no namespace or dots' % content_spec
