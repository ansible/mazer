
import logging
import mock
import tempfile

from ansible_galaxy.actions import install
from ansible_galaxy.models.context import GalaxyContext
from ansible_galaxy.flat_rest_api.content import GalaxyContent

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
    ret = install._build_content_set(['blrp'], 'role', galaxy_context)
    log.debug('ret: %s', ret)
    # TODO: eventually this should fail, depending on where it looks it up
    assert isinstance(ret[0], GalaxyContent)
    assert ret[0].name == 'blrp'
