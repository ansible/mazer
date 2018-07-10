
import logging
import mock

from ansible_galaxy.actions import info

log = logging.getLogger(__name__)


def display_callback(msg, **kwargs):
    log.debug(msg)


def test_info_empty(galaxy_context):
    ret = info.info_content_specs(galaxy_context,
                                  # mock api
                                  mock.Mock(),
                                  [],
                                  display_callback=display_callback,
                                  offline=True)

    log.debug('ret: %s', ret)


def test_info(galaxy_context):
    ret = info.info_content_specs(galaxy_context,
                                  # mock api
                                  mock.Mock(),
                                  ['namespace.repo.content'],
                                  display_callback=display_callback,
                                  offline=True)

    log.debug('ret: %s', ret)
