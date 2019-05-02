import logging

from ansible_galaxy.actions import publish

log = logging.getLogger(__name__)


def display_callback(msg, **kwargs):
    log.debug(msg)


def test_publish(galaxy_context, mocker):
    publish_api_key = "doesnt_matter_not_used"

    mocker.patch('ansible_galaxy.actions.publish.GalaxyAPI.publish_file',
                 return_value={"task": "/api/v2/collection-imports/123456789"})
    res = publish.publish(galaxy_context, "/dev/null", publish_api_key, display_callback)

    log.debug('res: %s', res)
    assert res == 0


def test__publish(galaxy_context, mocker):
    publish_api_key = "doesnt_matter_not_used"

    mocker.patch('ansible_galaxy.actions.publish.GalaxyAPI.publish_file',
                 return_value={"task": "/api/v2/collection-imports/8675309"})
    res = publish._publish(galaxy_context, "/dev/null", publish_api_key, display_callback)

    log.debug('res: %s', res)
    assert res['errors'] == []
    assert res['success'] is True
    assert res['response_data']['task'] == "/api/v2/collection-imports/8675309"

# TODO: test error paths
