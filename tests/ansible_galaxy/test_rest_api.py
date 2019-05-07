import io
import logging
import sys

import pytest

import requests
from six import text_type

import ansible_galaxy
from ansible_galaxy import exceptions
from ansible_galaxy import multipart_form
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
    context = GalaxyContext(collections_path=galaxy_context.collections_path,
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
    url = 'http://bogus.invalid:9443/api/'

    response_data = {
        'code': 'error',
        'message': 'A server error occurred.',
        'errors': [
            {'code': 'error', 'message': 'Error message 1.'},
            {'code': 'error', 'message': 'Stuff broke, 500 error but server response has valid json include the detail key'},
        ]
    }

    requests_mock.get(url,
                      json=response_data,
                      reason='Internal Server Ooopsie',
                      status_code=500)

    api = rest_api.GalaxyAPI(galaxy_context_example_invalid)

    with pytest.raises(exceptions.GalaxyRestAPIError,
                       match='.*500 Server Error: Internal Server Ooopsie for url.*bogus.invalid:9443.*') as exc_info:

        api._get_server_api_version()

    log.debug('exc_info: %s', exc_info)

    exc = exc_info.value

    log.debug('exc.response: %s', exc.response)
    log.debug('exc.request: %s', exc.request)

    assert exc.code == 'error'
    assert exc.message == 'A server error occurred.'
    assert isinstance(exc.errors, list)

    assert exc.request.url == url
    assert exc.response.status_code == 500
    assert exc.response.reason == 'Internal Server Ooopsie'
    assert exc.response.json()['code'] == 'error'
    assert exc.response.json()['errors'][0]['message'] == 'Error message 1.'


def test_galaxy_api_get_server_api_version_HTTPError_not_json(galaxy_context_example_invalid, requests_mock):
    url = 'http://bogus.invalid:9443/api/'
    requests_mock.get(url,
                      text='{stuff-that-is-not-valid-json',
                      reason='Internal Server Ooopsie',
                      status_code=500)

    api = rest_api.GalaxyAPI(galaxy_context_example_invalid)

    with pytest.raises(exceptions.GalaxyRestServerError,
                       match='.*500 Server Error: Internal Server Ooopsie for url.*bogus.invalid:9443.*') as exc_info:

        api._get_server_api_version()

    log.debug('exc_info: %s', exc_info)

    exc = exc_info.value

    log.debug('exc.response: %s', exc.response)
    log.debug('exc.request: %s', exc.request)

    assert exc.request.url == url
    assert exc.response.status_code == 500
    assert exc.response.reason == 'Internal Server Ooopsie'


def test_galaxy_api_get_server_api_version_no_current_version(galaxy_context_example_invalid, requests_mock):
    requests_mock.get('http://bogus.invalid:9443/api/',
                      json={'some_key': 'some_value',
                            'but_not_current_value': 2},
                      status_code=200)

    api = rest_api.GalaxyAPI(galaxy_context_example_invalid)

    with pytest.raises(exceptions.GalaxyClientError,
                       match="The Galaxy API version could not be determined. The required 'current_version' field is missing.*") as exc_info:
        api._get_server_api_version()

    log.debug('exc_info: %s', exc_info)


def test_galaxy_api_properties(galaxy_api):
    log.debug('api_server: %s', galaxy_api.api_server)
    log.debug('validate_certs: %s', galaxy_api.rest_client.validate_certs)

    assert galaxy_api.api_server == default_server_dict['url']
    assert galaxy_api.rest_client.validate_certs is True


@pytest.fixture
def galaxy_api_mocked(mocker, galaxy_context_example_invalid, requests_mock):
    requests_mock.get('http://bogus.invalid:9443/api/',
                      json={'current_version': 'v2'})

    api = rest_api.GalaxyAPI(galaxy_context_example_invalid)

    return api


@pytest.fixture
def file_upload_form():
    data = {
        'sha256': 'f9e588573f5e45b0640abe9eb0a82537c258c65a41a81d184984da28630a35db'
    }

    form = multipart_form.MultiPartForm()
    for key in data:
        form.add_field(key, data[key])

    # ('file', 'foo.tar.gz', some_fd, 'application/octetstream')
    # artifact_file_info = multipart_form.form_add_file_args(archive_path, mimetype='application/octet-stream')
    some_fd = io.BytesIO(b'Some bytes from a tar.gz')
    form.add_file('file', 'somens-somename-1.2.3.tar.gz', some_fd, 'application/octet-stream')

    return form


def test_galaxy_api_publish_file_202(galaxy_api_mocked, requests_mock, tmpdir, file_upload_form):
    status_202_json = {"task": "https://galaxy-dev.ansible.com/api/v2/collection-imports/224/"}

    # POST http://bogus.invalid:9443/api/v2/collections/
    requests_mock.post('http://bogus.invalid:9443/api/v2/collections/',
                       status_code=202,
                       json=status_202_json)

    publish_api_key = '1f107befb89e0863829264d5241111a'
    res = galaxy_api_mocked.publish_file(form=file_upload_form, publish_api_key=publish_api_key)

    log.debug('res: %s', res)

    assert isinstance(res, dict)
    assert res == status_202_json


def test_galaxy_api_publish_file_conflict_409(galaxy_api_mocked, requests_mock, tmpdir, file_upload_form):
    err_409_conflict_json = {'code': 'conflict.collection_exists', 'message': 'Collection "testing-ansible_testing_content-4.0.4" already exists.'}

    # POST http://bogus.invalid:9443/api/v2/collections/
    requests_mock.post('http://bogus.invalid:9443/api/v2/collections/',
                       status_code=409,
                       json=err_409_conflict_json)

    with pytest.raises(ansible_galaxy.exceptions.GalaxyPublishError) as exc_info:
        galaxy_api_mocked.publish_file(form=file_upload_form, publish_api_key=None)

    log.debug('exc_info:%s', exc_info)


def test_galaxy_api_publish_file_unauthorized_401(galaxy_api_mocked, requests_mock, tmpdir, file_upload_form):
    err_401_unauthorized_json = {'code': 'authentication_failed', 'message': 'Invalid token.'}

    # POST http://bogus.invalid:9443/api/v2/collections/
    requests_mock.post('http://bogus.invalid:9443/api/v2/collections/',
                       status_code=401,
                       reason='Unauthorized',
                       json=err_401_unauthorized_json)

    bad_publish_api_key = '1f107deadbeefcafee0863829264d5211a'
    with pytest.raises(ansible_galaxy.exceptions.GalaxyPublishError) as exc_info:
        galaxy_api_mocked.publish_file(form=file_upload_form, publish_api_key=bad_publish_api_key)

    log.debug('exc_info:%s', exc_info)


def test_galaxy_api_publish_file_request_error(galaxy_api_mocked, requests_mock, tmpdir, file_upload_form):

    # POST http://bogus.invalid:9443/api/v2/collections/
    # requests_mock.get('http://bogus.invalid:9443/api/',
    #                  exc=requests.
    exc = exceptions.GalaxyClientAPIConnectionError(requests.exceptions.SSLError('SSL stuff broke'))
    requests_mock.post('http://bogus.invalid:9443/api/v2/collections/',
                       exc=exc)

    publish_api_key = '1f107befb89e0863829264d5241111a'

    with pytest.raises(ansible_galaxy.exceptions.GalaxyClientAPIConnectionError) as exc_info:
        galaxy_api_mocked.publish_file(form=file_upload_form, publish_api_key=publish_api_key)

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
    url = 'http://bogus.invalid:9443/api/v2/collections/alikins/some_collection_that_doesnt_exist'
    requests_mock.get(url,
                      status_code=404,
                      reason='Not Found',
                      json={'code': 'not_found',
                            'message': 'Not found.'})

    namespace = 'alikins'
    name = 'some_collection_that_doesnt_exist'

    with pytest.raises(exceptions.GalaxyRestAPIError) as exc_info:
        galaxy_api.get_collection_detail(namespace, name)

    log.debug('exc_info: %s', exc_info)

    exc = exc_info.value

    assert exc.code == 'not_found'
    assert exc.message == 'Not found.'
    assert isinstance(exc.errors, list)

    assert exc.request.url == url
    assert exc.response.status_code == 404
    assert exc.response.reason == 'Not Found'
    assert exc.response.json()['code'] == 'not_found'


def test_get_object(galaxy_api_mocked, requests_mock):
    url = 'http://bogus.invalid:9443/api/v3/unicorns/sparkleland/magestic/versions/1.0.0/'

    requests_mock.get(url,
                      status_code=200,
                      reason='OK',
                      json={'stuff': [3, 4, 5]})

    data = galaxy_api_mocked.get_object(href=url)

    assert data['stuff'] == [3, 4, 5]


def test_get_object_list(galaxy_api_mocked, requests_mock):
    url = 'http://bogus.invalid:9443/api/v3/unicorns/sparkleland/magestic/'

    requests_mock.get(url,
                      status_code=200,
                      reason='OK',
                      json=[{'stuff': [3, 4, 5]},
                            {'stuff': [1, 2, 3]}])

    data = galaxy_api_mocked.get_object(href=url)

    log.debug('data:\n%s', data)

    assert isinstance(data, list)
    assert data[0]['stuff'] == [3, 4, 5]
    assert data[1]['stuff'] == [1, 2, 3]


def test_get_object_redirect_302(galaxy_api_mocked, requests_mock):
    url = 'http://bogus.invalid:9443/api/v3/unicorns/sparkleland/magestic/versions/1.0.0/artifact/'
    new_url = 'https://bogus.invalid:9443/box_of_unicorns/f7325978-5339-4669-b7a4-a9406f32994f'
    requests_mock.get(url,
                      status_code=302,
                      reason='Found',
                      headers={'location': new_url})

    requests_mock.get(new_url,
                      status_code=200,
                      reason='OK',
                      json={'unicorn_stuff': [5, 10, 15]})

    data = galaxy_api_mocked.get_object(href=url)

    log.debug('data:\n%s', data)

    assert data['unicorn_stuff'] == [5, 10, 15]


def test_get_object_redirect_301(galaxy_api_mocked, requests_mock):
    url = 'http://bogus.invalid:9443/api/v3/unicorns/sparkleland/magestic/versions/1.0.0/artifact/'
    ssl_url = 'https://bogus.invalid:9443/api/v3/unicorns/sparkleland/magestic/versions/1.0.0/artifact/'
    requests_mock.get(url,
                      status_code=301,
                      reason='Permanently Moved',
                      headers={'location': ssl_url})

    requests_mock.get(ssl_url,
                      status_code=200,
                      reason='OK',
                      json={'unicorn_stuff': [5, 10, 15]})

    data = galaxy_api_mocked.get_object(href=url)

    log.debug('data:\n%s', data)

    assert data['unicorn_stuff'] == [5, 10, 15]


def test_get_object_dict_with_results_but_not_paginated(galaxy_api_mocked, requests_mock):
    url = 'http://bogus.invalid:9443/api/v3/unicorns/sparkleland/magestic/enemies/'

    response_data = {
        "results": [
            {'stuff': [3, 4, 5]},
            {'stuff': [1, 2, 3]}
        ]
    }

    requests_mock.get(url,
                      status_code=200,
                      reason='OK',
                      json=response_data,)

    data = galaxy_api_mocked.get_object(href=url)

    log.debug('data:\n%s', data)

    assert isinstance(data, dict)
    assert data['results'][0]['stuff'] == [3, 4, 5]
    assert data['results'][1]['stuff'] == [1, 2, 3]


def test_get_object_paginated(galaxy_api_mocked, requests_mock):
    url_page1 = 'http://bogus.invalid:9443/api/v3/unicorns/sparkleland/magestic/versions/'

    response_data_page1 = {
        "count": 5,
        "next": "http://localhost:8000/api/v2/collections/alikins/collection_ntp/versions/?page=2&page_size=3",
        "previous": None,
        "results": [
            {
                "version": "0.1.181",
                "href": "http://localhost:8000/api/v2/collections/alikins/collection_ntp/versions/0.1.181/"
            },
            {
                "version": "0.1.177",
                "href": "http://localhost:8000/api/v2/collections/alikins/collection_ntp/versions/0.1.177/"
            },
            {
                "version": "0.1.176",
                "href": "http://localhost:8000/api/v2/collections/alikins/collection_ntp/versions/0.1.176/"
            }
        ]
    }

    url_page2 = 'http://localhost:8000/api/v2/collections/alikins/collection_ntp/versions/?page=2&page_size=3'

    response_data_page2 = {
        "count": 5,
        "next": None,
        "previous": "http://localhost:8000/api/v2/collections/alikins/collection_ntp/versions/?page_size=3",
        "results": [
            {
                "version": "0.1.175",
                "href": "http://localhost:8000/api/v2/collections/alikins/collection_ntp/versions/0.1.175/"
            },
            {
                "version": "0.1.173",
                "href": "http://localhost:8000/api/v2/collections/alikins/collection_ntp/versions/0.1.173/"
            },
        ]
    }

    requests_mock.get(url_page1,
                      status_code=200,
                      reason='OK',
                      json=response_data_page1)

    requests_mock.get(url_page2,
                      status_code=200,
                      reason='OK',
                      json=response_data_page2)

    data = galaxy_api_mocked.get_object(href=url_page1)

    import json
    log.debug('data:\n%s', json.dumps(data, indent=4))
    log.debug('len: %s', len(data))

    assert len(data) == 5
    assert data[0]['version'] == '0.1.181'
    assert data[2]['version'] == '0.1.176'
    assert data[4]['version'] == '0.1.173'


def test_get_object_paginated_error_on_second_request(galaxy_api_mocked, requests_mock):
    url_page1 = 'http://bogus.invalid:9443/api/v3/even_numbers/'

    response_data_page1 = {
        "count": 5,
        "next": "http://bogus.invalid:9443/api/v3/even_numbers/?page=2&page_size=2",
        "previous": None,
        "results": [4, 6]
    }

    url_page2 = 'http://bogus.invalid:9443/api/v3/even_numbers/?page=2&page_size=2'

    requests_mock.get(url_page1,
                      status_code=200,
                      reason='OK',
                      json=response_data_page1)

    requests_mock.get(url_page2,
                      status_code=500,
                      reason='error',
                      json={'code': 'error',
                            'message': 'This server does not count very well. Sorry.'})

    with pytest.raises(exceptions.GalaxyRestAPIError) as exc_info:
        galaxy_api_mocked.get_object(href=url_page1)

    exc = exc_info.value

    import json
    log.debug('resp.json:\n%s', json.dumps(exc.response.json(), indent=4))

    assert exc.code == 'error'
    assert exc.message == 'This server does not count very well. Sorry.'
    assert isinstance(exc.errors, list)
    assert exc.response.url == 'http://bogus.invalid:9443/api/v3/even_numbers/?page=2&page_size=2'

    log.debug('exc: %s', exc)

    assert 'http://bogus.invalid:9443/api/v3/even_numbers/?page=2&page_size=2' in str(exc)


def test_get_object_403(galaxy_api_mocked, requests_mock):
    url = 'http://bogus.invalid:9443/api/v3/invisible_unicorns/narnia/aurora/versions/51.51.51/'

    error_dict = {'code': 'permission_denied',
                  'message': 'You do not have permission to see this invisble unicorn.'}
    requests_mock.get(url,
                      status_code=403,
                      reason='Permission denied',
                      json=error_dict,)

    with pytest.raises(exceptions.GalaxyRestAPIError) as exc_info:
        galaxy_api_mocked.get_object(href=url)

    log.debug('exc_info: %s', exc_info)

    exc = exc_info.value

    assert exc.code == 'permission_denied'
    assert exc.message == 'You do not have permission to see this invisble unicorn.'
    assert isinstance(exc.errors, list)
    assert exc.errors == []

    log.debug('exc.response: %s', exc.response)
    log.debug('exc.request: %s', exc.request)

    assert exc.request.url == url
    assert exc.response.status_code == 403
    assert exc.response.reason == 'Permission denied'
    assert exc.response.json() == error_dict


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
                      reason='Bad Request',
                      json=response_data)

    with pytest.raises(exceptions.GalaxyRestAPIError) as exc_info:
        galaxy_api_mocked.get_object(href=url)

    log.debug('exc_info: %s', exc_info)

    exc = exc_info.value

    assert exc.code == 'invalid'
    assert exc.message == 'Invalid input.'
    assert isinstance(exc.errors, list)
    assert exc.errors[0]['message'] == 'First bar message.'

    assert exc.request.url == url
    assert exc.response.status_code == 400
    assert exc.response.reason == 'Bad Request'
    assert exc.response.json()['code'] == 'invalid'


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
                      reason='Internal Server Ooopsie',
                      json=response_data)

    with pytest.raises(exceptions.GalaxyRestAPIError) as exc_info:
        galaxy_api_mocked.get_object(href=url)

    log.debug('exc_info: %s', exc_info)

    exc = exc_info.value

    assert exc.code == 'error'
    assert exc.message == 'A server error occurred.'
    assert isinstance(exc.errors, list)

    assert exc.errors[1]['message'] == 'DOES NOT COMPUTE!'


# # FIXME:use mocked requests.Response, set status. requests wont raise an exception so side_effect is wrong
def test_get_object_500_json_not_dict(galaxy_api_mocked, requests_mock):
    url = 'http://bogus.invalid:9443/api/v2/collections/alikins/some_collection'

    requests_mock.get(url,
                      status_code=500,
                      reason='Internal Server Ooopsie',
                      json=[])

    # ansible_galaxy.exceptions.GalaxyRestAPIError:
    # 500 Server Error: Internal Server Ooopsie for url: http://bogus.invalid:9443/api/v2/collections/alikins/some_collection
    with pytest.raises(exceptions.GalaxyRestAPIError) as exc_info:
        galaxy_api_mocked.get_object(href=url)

    log.debug('exc_info: %s', exc_info)

    exc = exc_info.value

    # ie, this error resonse was not in the expected {'code':...} style data structure
    assert exc.code == 'unknown_api_error'
    assert exc.message == 'A Galaxy REST API error.'
    assert isinstance(exc.errors, list)
    assert exc.errors == []


def test_get_object_500_with_junk(galaxy_api_mocked, requests_mock):
    url = 'http://bogus.invalid:9443/api/v22/rhymes/purple/'

    # partial json
    response_text = r'''{"code": "error", ['''

    requests_mock.get(url,
                      status_code=500,
                      reason='Internal Server Ooopsie',
                      text=response_text)

    # exc str(): Could not process data from the API server (http://bogus.invalid:9443/api/v24/rhymes/orange/): Expecting value: line 1 column 1 (char 0)
    with pytest.raises(exceptions.GalaxyRestServerError,
                       match='.*500 Server Error: Internal Server Ooopsie for url.*bogus.invalid:9443.*') as exc_info:

        galaxy_api_mocked.get_object(href=url)

    log.debug('exc_info: %s', exc_info)


def test_get_object_500_with_html(galaxy_api_mocked, requests_mock):
    url = 'http://bogus.invalid:9443/api/v24/rhymes/orange/'

    # despite asking for json, the 500 response is html
    response_text = r'''<h1>Server Error (500)</h1>'''
    requests_mock.get(url,
                      status_code=500,
                      reason='Internal Server Ooopsie',
                      headers={'content-type': 'text/html; charset=UTF-8'},
                      text=response_text)

    # exc str(): Could not process data from the API server (http://bogus.invalid:9443/api/v24/rhymes/orange/): Expecting value: line 1 column 1 (char 0)
    with pytest.raises(exceptions.GalaxyRestServerError,
                       match='.*500 Server Error: Internal Server Ooopsie for url.*bogus.invalid:9443.*') as exc_info:
        galaxy_api_mocked.get_object(href=url)

    log.debug('exc_info: %s', exc_info)


def test_galaxy_api_get_collection_detail_SSLError(mocker, galaxy_api, requests_mock):
    ssl_msg = 'ssl stuff broke... good luck and godspeed.'
    requests_mock.get('http://bogus.invalid:9443/api/v2/collections/some-test-namespace/some-test-name',
                      exc=requests.exceptions.SSLError(ssl_msg)
                      )

    # ansible_galaxy.exceptions.GalaxyClientAPIConnectionError: ssl stuff broke... good luck and godspeed.
    with pytest.raises(exceptions.GalaxyClientAPIConnectionError, match='.*%s.*' % ssl_msg) as exc_info:
        galaxy_api.get_collection_detail('some-test-namespace', 'some-test-name')

    log.debug('exc_info: %s', exc_info)


def test_user_agent():
    res = rest_api.user_agent()
    assert res.startswith('Mazer/%s' % ansible_galaxy.__version__)
    assert sys.platform in res
    assert 'python:' in res
    assert 'ansible_galaxy' in res
