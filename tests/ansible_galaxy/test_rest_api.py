import io
import json
import logging
import ssl
import sys

import pytest

from six import text_type

import ansible_galaxy
from ansible_galaxy import exceptions
from ansible_galaxy.models.context import GalaxyContext
from ansible_galaxy import rest_api

log = logging.getLogger(__name__)


def test_galaxy_api_init():

    gc = GalaxyContext()
    api = rest_api.GalaxyAPI(gc)

    assert isinstance(api, rest_api.GalaxyAPI)
    assert api.galaxy_context == gc


default_server_dict = {'url': 'http://bogus.invalid:9443',
                       'ignore_certs': False}


@pytest.fixture
def galaxy_context_example_invalid(galaxy_context):
    context = GalaxyContext(content_path=galaxy_context.content_path,
                            server={'url': default_server_dict['url'],
                                    'ignore_certs': False})
    return context


@pytest.fixture
def galaxy_api(galaxy_context_example_invalid, requests_mock):

    # mock the result of _get_server_api_versions here, so that we dont get the extra
    # call when calling the tests

    requests_mock.get('http://bogus.invalid:9443/api/',
                      json={'current_version': 'v1'})
    requests_mock.get('http://bogus.invalid:9443/api/whatever/',
                      json={'results': [{'foo1': 11,
                                         'foo2': 12}
                                        ]
                            })

    api = rest_api.GalaxyAPI(galaxy_context_example_invalid)

    # do a call so that we run g_connect and _get_server_api_versions by side effect now
    # api.get_object(href='http://bogus.invalid:9443/api/whatever/')

    log.debug('api: %s', api)

    yield api


def test_galaxy_api_get_server_api_version(galaxy_context_example_invalid, requests_mock):
    requests_mock.get('http://bogus.invalid:9443/api/',
                      json={'current_version': 'v1'})

    api = rest_api.GalaxyAPI(galaxy_context_example_invalid)
    res = api._get_server_api_version()

    log.debug('res: %s %r', res, res)

    assert isinstance(res, text_type)
    assert res == 'v1'


def test_galaxy_api_get_server_api_version_not_supported_version(galaxy_context_example_invalid, requests_mock):
    requests_mock.get('http://bogus.invalid:9443/api/',
                      json={'current_version': 'v11.22.13beta4.preRC-16.0.0.0.42.42.37.1final'})

    api = rest_api.GalaxyAPI(galaxy_context_example_invalid)

    # expected to raise a client error about the server version not being supported in client
    # TODO: should be the server deciding if the client version is sufficient
    with pytest.raises(exceptions.GalaxyClientError, match='.*Unsupported Galaxy server API.*') as exc_info:
        api.get_collection_detail('test-namespace', 'test-repo')

    log.debug('exc_info: %s', exc_info)


def test_galaxy_api_get_server_api_version_HTTPError_500(galaxy_context_example_invalid, requests_mock):
    data = {"detail": "Stuff broke, 500 error but server response has valid json include the detail key"}
    requests_mock.get('http://bogus.invalid:9443/api/',
                      json=data,
                      status_code=500)

    api = rest_api.GalaxyAPI(galaxy_context_example_invalid)

    try:
        api._get_server_api_version()
    except exceptions.GalaxyClientError as e:
        log.exception(e)
        # fragile, but currently return same exception so look for the right msg in args
        assert 'Failed to get data from the API server' in '%s' % e
        return

    assert False, 'Expected a GalaxyClientError here but that did not happen'


def test_galaxy_api_get_server_api_version_HTTPError_not_json(galaxy_context_example_invalid, requests_mock):
    requests_mock.get('http://bogus.invalid:9443/api/',
                      text='{stuff-that-is-not-valid-json',
                      status_code=500)

    api = rest_api.GalaxyAPI(galaxy_context_example_invalid)

    try:
        api._get_server_api_version()
    except exceptions.GalaxyClientError as e:
        log.exception(e)
        # fragile, but currently return same exception so look for the right msg in args
        assert 'Could not process data from the API server' in '%s' % e

        return

    assert False, 'Expected a GalaxyClientError here but that did not happen'


def test_galaxy_api_get_server_api_version_no_current_version(galaxy_context_example_invalid, requests_mock):
    requests_mock.get('http://bogus.invalid:9443/api/',
                      json={'some_key': 'some_value',
                            'but_not_current_value': 2},
                      status_code=200)

    api = rest_api.GalaxyAPI(galaxy_context_example_invalid)
    try:
        api._get_server_api_version()
    except exceptions.GalaxyClientError as e:
        log.exception(e)
        # fragile, but currently return same exception so look for the right msg in args
        assert "missing required 'current_version'" in '%s' % e

        return

    assert False, 'Expected a GalaxyClientError here but that did not happen'


def test_galaxy_api_properties(galaxy_api):
    log.debug('api_server: %s', galaxy_api.api_server)
    log.debug('validate_certs: %s', galaxy_api.validate_certs)

    assert galaxy_api.api_server == default_server_dict['url']
    assert galaxy_api.validate_certs is True


@pytest.fixture
def galaxy_api_mocked(mocker, galaxy_context_example_invalid, requests_mock):
    mocker.patch('ansible_galaxy.rest_api.MultiPartForm.add_file')
    mocker.patch('ansible_galaxy.rest_api.MultiPartForm.get_binary',
                 return_value=io.BytesIO())
    mocker.patch('ansible_galaxy.rest_api.GalaxyAPI._form_add_file_args',
                 return_value=('file', 'dummy args', None, 'application/octet-stream'))

    requests_mock.get('http://bogus.invalid:9443/api/',
                      json={'current_version': 'v2'})

    api = rest_api.GalaxyAPI(galaxy_context_example_invalid)

    return api


def test_galaxy_api_publish_file_202(galaxy_api_mocked, requests_mock, tmpdir):
    status_202_json = {"task": "https://galaxy-dev.ansible.com/api/v2/collection-imports/224/"}

    # POST http://bogus.invalid:9443/api/v2/collections/
    requests_mock.post('http://bogus.invalid:9443/api/v2/collections/',
                       status_code=202,
                       json=status_202_json)

    res = galaxy_api_mocked.publish_file(data={}, archive_path=None, publish_api_key=None)

    log.debug('res: %s', res)

    assert isinstance(res, text_type)
    assert json.loads(res) == status_202_json


def test_galaxy_api_publish_file_conflict_409(galaxy_api_mocked, requests_mock, tmpdir):
    err_409_conflict_json = {'code': 'conflict.collection_exists', 'message': 'Collection "testing-ansible_testing_content-4.0.4" already exists.'}

    # POST http://bogus.invalid:9443/api/v2/collections/
    requests_mock.post('http://bogus.invalid:9443/api/v2/collections/',
                       status_code=409,
                       json=err_409_conflict_json)

    with pytest.raises(ansible_galaxy.exceptions.GalaxyPublishError) as exc_info:
        galaxy_api_mocked.publish_file(data={}, archive_path=None, publish_api_key=None)

    log.debug('exc_info:%s', exc_info)


def test_galaxy_api_get_collection_detail(mocker, galaxy_api, requests_mock):
    data_dict = {
        "id": 24,
        "href": "http://bogus.invalid:9443/api/v2/collections/ansible/k8s/",
        "name": "k8s",
        "namespace": {
            "id": 12,
            "href": "http://bogus.invalid:9443/api/v2/namespaces/ansible/",
            "name": "ansible",
        },
        "versions_url": "http://bogus.invalid:9443/api/v2/collections/ansible/k8s/versions/",
        "highest_version": {
            "version": "4.2.0",
            "href": "http://bogus.invalid:9443/api/v2/collections/ansible/k8s/versions/4.2.0",
        },
        "deprecated": "false",
        "created": "2019-03-15T10:05:11.589728-04:00",
        "modified": "2019-03-22T10:05:11.589728-04:00",
    }

    requests_mock.get('http://bogus.invalid:9443/api/v2/collections/ansible/k8s',
                      json=data_dict)

    namespace = 'ansible'
    name = 'k8s'
    res = galaxy_api.get_collection_detail(namespace, name)

    log.debug('res: %s', res)

    # FIXME: lookup_content_by_name only returns the first result
    assert isinstance(res, dict)
    assert res['id'] == 24
    assert 'highest_version' in res
    assert res['href'] == "http://bogus.invalid:9443/api/v2/collections/ansible/k8s/"


def test_galaxy_api_get_collection_detail_empty_results(mocker, galaxy_api, requests_mock):
    requests_mock.get('http://bogus.invalid:9443/api/v2/collections/alikins/role-awx',
                      json={})

    namespace = 'alikins'
    name = 'role-awx'
    res = galaxy_api.get_collection_detail(namespace, name)

    log.debug('res: %s', res)

    # If there are no results, we expect to get back an empty dict.
    # FIXME: should probably return the full list and let the app care what that means
    assert isinstance(res, dict)
    assert res == {}


def test_galaxy_api_get_collection_detail_404(mocker, galaxy_api, requests_mock):

    requests_mock.get('http://bogus.invalid:9443/api/v2/collections/alikins/some_collection_that_doesnt_exist',
                      status_code=404,
                      json={'code': 'not_found',
                            'message': 'Not found.'})

    namespace = 'alikins'
    name = 'some_collection_that_doesnt_exist'
    res = galaxy_api.get_collection_detail(namespace, name)

    log.debug('res: %s', res)

    assert isinstance(res, dict)
    assert res['code'] == 'not_found'


def test_get_object(galaxy_api_mocked, requests_mock):
    url = 'http://bogus.invalid:9443/api/v3/unicorns/sparkleland/magestic/versions/1.0.0/'

    requests_mock.get(url,
                      status_code=200,
                      json={'stuff': [3, 4, 5]})

    data = galaxy_api_mocked.get_object(href=url)

    assert data['stuff'] == [3, 4, 5]


def test_get_object_403(galaxy_api_mocked, requests_mock):
    url = 'http://bogus.invalid:9443/api/v3/invisible_unicorns/narnia/aurora/versions/51.51.51/'

    requests_mock.get(url,
                      status_code=403,
                      json={'code': 'permission_denied',
                            'message': 'You do not have permission to see this invisble unicorn.'})

    data = galaxy_api_mocked.get_object(href=url)

    log.debug('data: %s', data)
    assert data['code'] == 'permission_denied'


def test_get_object_400_validation_error(galaxy_api_mocked, requests_mock):
    url = 'http://bogus.invalid:9443/api/v3/apples/'

    response_data = \
        {'code': 'invalid',
         'message': 'Invalid input.',
         'errors': [
             {
                 'code': 'conflict',
                 'message': 'First bar message.',
                 'field': 'bar',
             },
             {
                 'code': 'invalid',
                 'message': 'Foo error message.',
                 'field': 'foo'
             },
             {
                 'code': 'invalid',
                 'message': 'Other message.'
             },
             {
                 'code': 'invalid',
                 'message': 'Second bar message.',
                 'field': 'bar'
             },
         ]
         }

    requests_mock.get(url,
                      status_code=400,
                      json=response_data)

    data = galaxy_api_mocked.get_object(href=url)

    log.debug('data: %s', data)
    assert data['code'] == 'invalid'
    assert isinstance(data['errors'], list)
    assert data['errors'][0]['message'] == 'First bar message.'


def test_get_object_500_with_body(galaxy_api_mocked, requests_mock):
    url = 'http://bogus.invalid:9443/api/v22/answers/?question=why'
    response_data = {
        'code': 'error',
        'message': 'A server error occurred.',
        'errors': [
            {'code': 'error', 'message': 'Error message 1.'},
            {'code': 'error', 'message': 'DOES NOT COMPUTE!'},
        ]
    }

    requests_mock.get(url,
                      status_code=500,
                      json=response_data)

    data = galaxy_api_mocked.get_object(href=url)

    log.debug('data: %s', data)
    assert data['code'] == 'error'
    assert isinstance(data['errors'], list)


def test_get_object_500_with_junk(galaxy_api_mocked, requests_mock):
    url = 'http://bogus.invalid:9443/api/v22/rhymes/purple/'

    # partial json
    response_text = r'''{"code": "error", ['''

    requests_mock.get(url,
                      status_code=500,
                      text=response_text)

    data = galaxy_api_mocked.get_object(href=url)

    log.debug('data: %s', data)

    # TODO: for now, a 500 with bogus json body will return an empty dict,
    #       but should be updated to raise an exception?
    assert data == {}


def test_get_object_500_with_html(galaxy_api_mocked, requests_mock):
    url = 'http://bogus.invalid:9443/api/v24/rhymes/orange/'

    # despite asking for json, the 500 response is html
    response_text = r'''<h1>Server Error (500)</h1>'''
    requests_mock.get(url,
                      status_code=500,
                      headers={'content-type': 'text/html; charset=UTF-8'},
                      text=response_text)

    data = galaxy_api_mocked.get_object(href=url)

    log.debug('data: %s', data)

    # TODO: for now, a 500 with bogus json body will return an empty dict,
    #       but should be updated to raise an exception?
    assert data == {}


# # FIXME:use mocked requests.Response, set status. requests wont raise an exception so side_effect is wrong
# def test_galaxy_api_get_collection_detail_500_json_not_dict(mocker, galaxy_api):
#     mocker.patch('ansible_galaxy.rest_api.requests.Session.request',
#                  side_effect=HTTPError(url='http://whatever',
#                                        code=500,
#                                        msg='Stuff broke.',
#                                        hdrs={},
#                                        fp=io.StringIO(initial_value=u'[]')))

#     try:
#         galaxy_api.get_collection_detail('some-test-namespace', 'some-test-name')
#     except exceptions.GalaxyClientError as e:
#         log.exception(e)
#         log.debug(e)
#         return

#     assert False, 'Excepted to get a HTTPError(code=500) here but did not.'


# FIXME: return mocked requests.Response, rm side_effect
# def test_galaxy_api_get_collection_detail_500_json(mocker, galaxy_api):
#     error_body_text = u'{"detail": "Stuff broke, 500 error but server response has valid json include the detail key"}'

#     mocker.patch('ansible_galaxy.rest_api.requests.Session.request',
#                  side_effect=HTTPError(url='http://whatever',
#                                        code=500,
#                                        msg='Stuff broke.',
#                                        hdrs={},
#                                        fp=io.StringIO(initial_value=error_body_text)))

#     try:
#         galaxy_api.get_collection_detail('some-test-namespace', 'some-test-name')
#     except exceptions.GalaxyClientError as e:
#         log.exception(e)
#         log.debug(e)
#         return

#     assert False, 'Excepted to get a GalaxyClientError here but did not.'


def test_galaxy_api_get_collection_detail_SSLError(mocker, galaxy_api, requests_mock):
    ssl_msg = 'ssl stuff broke... good luck and godspeed.'
    requests_mock.get('http://bogus.invalid:9443/api/v2/collections/some-test-namespace/some-test-name',
                      exc=ssl.SSLError(ssl_msg)
                      )

    with pytest.raises(exceptions.GalaxyClientAPIConnectionError, match='.*%s.*' % ssl_msg) as exc_info:
        galaxy_api.get_collection_detail('some-test-namespace', 'some-test-name')

    log.debug('exc_info: %s', exc_info)


def test_user_agent():
    res = rest_api.user_agent()
    assert res.startswith('Mazer/%s' % ansible_galaxy.__version__)
    assert sys.platform in res
    assert 'python:' in res
    assert 'ansible_galaxy' in res
