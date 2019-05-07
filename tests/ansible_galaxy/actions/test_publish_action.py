import logging
import os

from ansible_galaxy.actions import publish
from ansible_galaxy.models.context import GalaxyContext

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


def test__publish_api_error(galaxy_context, mocker, requests_mock):
    publish_api_key = "doesnt_matter_not_used"

    context = GalaxyContext(collections_path=galaxy_context.collections_path,
                            server={'url': 'http://notreal.invalid:8000',
                                    'ignore_certs': False})
    log.debug('galaxy_context: %s', context)

    err_409_conflict_json = {'code': 'conflict.collection_exists', 'message': 'Collection "testing-ansible_testing_content-4.0.4" already exists.'}
    requests_mock.get('http://notreal.invalid:8000/api/',
                      status_code=200,
                      json={'current_version': 'v1'})

    requests_mock.post('http://notreal.invalid:8000/api/v2/collections/',
                       status_code=409,
                       reason='Conflict',
                       json=err_409_conflict_json)

    res = publish._publish(context, "/dev/null", publish_api_key, display_callback)

    log.debug('res: %s', res)
    assert res['errors'] == ['Error publishing null to http://notreal.invalid:8000/api/v2/collections/ '
                             + '- Collection "testing-ansible_testing_content-4.0.4" already exists.']
    assert res['success'] is False


def test_publish_api_errors(mocker):
    error_msg = 'Error publishing ns-n-1.0.0 to http://notreal.invalid:8000/api/v2/collections/ - Collection "ns-n-1.0.0" already exists.'
    mocker.patch('ansible_galaxy.actions.publish._publish',
                 return_value={'errors':
                               [error_msg], 'success': False})

    mock_display_callback = mocker.Mock()

    context = None
    publish_api_key = None
    res = publish.publish(context, "/dev/null", publish_api_key, mock_display_callback)

    log.debug('res: %s', res)

    assert res == os.EX_SOFTWARE  # 70
    assert mock_display_callback.called is True


# TODO: test error paths
