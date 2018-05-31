
import logging
import mock
import tempfile

from ansible_galaxy.actions import info
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


def test_info_empty():
    ret = info.info_content_specs(_galaxy_context(),
                                  # mock api
                                  mock.Mock(),
                                  [],
                                  content_path=None,
                                  display_callback=display_callback,
                                  offline=True)

    log.debug('ret: %s', ret)


def test_info():
    ret = info.info_content_specs(_galaxy_context(),
                                  # mock api
                                  mock.Mock(),
                                  ['namespace.repo.content'],
                                  content_path=None,
                                  display_callback=display_callback,
                                  offline=True)

    log.debug('ret: %s', ret)
