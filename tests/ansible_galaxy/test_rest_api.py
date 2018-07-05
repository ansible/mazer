import io
import logging
import json
import ssl
import sys

import pytest
import mock

from six.moves.urllib.error import HTTPError
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
    assert api.galaxy == gc


class FauxUrlOpenResponse(object):
    def __init__(self, url=None, body=None, status=200, data=None, info=None, redirect_url=None):
        self.status = 200
        self.data = data
        if self.data is not None:
            self.body = json.dumps(self.data)
        else:
            self.body = body or ''
        self.url = url
        self._info = info
        self.redirect_url = redirect_url

    def read(self):
        # log.debug('read: %s %s', self.body, self)
        return self.body

    def getcode(self):
        log.debug('getcode: %s', self.status)
        return self.status

    def geturl(self):
        if self.redirect_url:
            log.debug('geturl: %s self: %s', self.redirect_url, self)
            return self.redirect_url

        log.debug('geturl: %s self: %s', self.url, self)
        return self.url

    def info(self):
        # log.debug('info: %s', self._info)
        return self._info

    def __repr__(self):
        return '%s(url="%s", status=%s, info="%s", body="%s", data="%s")' % \
            (self.__class__.__name__, self.url, self.status, self._info, self.body, self.data)


class FauxUrlResponder(object):
    def __init__(self, list_of_responses=None):
        self.responses = list_of_responses or []
        self.calls = []
        # log.debug('self.responses: %s', pprint.pformat(self.responses))

    def __call__(self, *args, **kwargs):
        next_response = self.responses.pop(0)

        # set the response url to the same as the request url
        url = args[0]

        next_response.url = url

        self.calls.append({'args': args,
                           'kwargs': kwargs,
                           'response': next_response})
        # log.debug('next_response: %s', next_response)
        return next_response

    def __repr__(self):
        return '%s(responses=%s)' % (self.__class__.__name__, self.responses)


default_server_dict = {'url': 'https://galaxy-qa.ansible.com',
                       'ignore_certs': False}


def test_galaxy_api_get_server_api_version(mocker):
    mocker.patch('ansible_galaxy.rest_api.open_url',
                 new=FauxUrlResponder(
                     [
                         FauxUrlOpenResponse(data={'current_version': 'v1'}),
                     ]
                 ))

    gc = GalaxyContext(server=default_server_dict)
    api = rest_api.GalaxyAPI(gc)
    res = api._get_server_api_version()

    log.debug('res: %s', res)

    assert isinstance(res, text_type)
    assert res == 'v1'


def test_galaxy_api_get_server_api_version_not_supported_version(mocker):
    mocker.patch('ansible_galaxy.rest_api.open_url',
                 new=FauxUrlResponder(
                     [
                         FauxUrlOpenResponse(data={'current_version': 'v11.22.13beta4.preRC-16.0.0.0.42.42.37.1final'}),
                         # doesn't matter response, just need a second call
                         FauxUrlOpenResponse(data={'results': 'stuff'},
                                             url='blippyblopfakeurl'),
                     ]
                 ))

    gc = GalaxyContext(server=default_server_dict)
    api = rest_api.GalaxyAPI(gc)

    # expected to raise a client error about the server version not being supported in client
    # TODO: should be the server deciding if the client version is sufficient
    try:
        api.lookup_repo_by_name('test-namespace', 'test-repo')
    except exceptions.GalaxyClientError as e:
        log.exception(e)
        assert 'Unsupported Galaxy server API' in '%s' % e
        return

    assert False, 'Expected a GalaxyClientError about supported server apis, but didnt happen'


def test_galaxy_api_get_server_api_version_HTTPError_500(mocker):
    error_body = u'{"detail": "Stuff broke, 500 error but server response has valid json include the detail key"}'

    mocker.patch('ansible_galaxy.rest_api.open_url',
                 side_effect=HTTPError(url='http://whatever',
                                       code=500,
                                       msg='Stuff broke.',
                                       hdrs={},
                                       fp=io.StringIO(initial_value=error_body)))

    gc = GalaxyContext(server=default_server_dict)
    api = rest_api.GalaxyAPI(gc)
    try:
        api._get_server_api_version()
    except exceptions.GalaxyClientError as e:
        log.exception(e)
        # fragile, but currently return same exception so look for the right msg in args
        assert 'Failed to get data from the API server' in '%s' % e
        return

    assert False, 'Expected a GalaxyClientError here but that did not happen'


def test_galaxy_api_get_server_api_version_HTTPError_not_json(mocker):
    mocker.patch('ansible_galaxy.rest_api.open_url',
                 new=FauxUrlResponder(
                     [
                         FauxUrlOpenResponse(status=500, body='{stuff-that-is-not-valid-json'),
                     ]
                 ))

    gc = GalaxyContext(server=default_server_dict)
    api = rest_api.GalaxyAPI(gc)
    try:
        api._get_server_api_version()
    except exceptions.GalaxyClientError as e:
        log.exception(e)
        # fragile, but currently return same exception so look for the right msg in args
        assert 'Could not process data from the API server' in '%s' % e

        return

    assert False, 'Expected a GalaxyClientError here but that did not happen'


def test_galaxy_api_get_server_api_version_no_current_version(mocker):
    mocker.patch('ansible_galaxy.rest_api.open_url',
                 new=FauxUrlResponder(
                     [
                         FauxUrlOpenResponse(status=500, data={'some_key': 'some_value',
                                                               'but_not_current_value': 2}),
                     ]
                 ))

    gc = GalaxyContext(server=default_server_dict)
    api = rest_api.GalaxyAPI(gc)
    try:
        api._get_server_api_version()
    except exceptions.GalaxyClientError as e:
        log.exception(e)
        # fragile, but currently return same exception so look for the right msg in args
        assert "missing required 'current_version'" in '%s' % e

        return

    assert False, 'Expected a GalaxyClientError here but that did not happen'


galaxy_context_params = [{'server': default_server_dict,
                          'content_dir': None}]


@pytest.fixture(scope='module',
                params=galaxy_context_params)
def galaxy_api(request):
    gc = GalaxyContext(server=request.param['server'])
    # log.debug('gc: %s', gc)

    # mock the result of _get_server_api_versions here, so that we dont get the extra
    # call when calling the tests

    patcher = mock.patch('ansible_galaxy.rest_api.open_url',
                         new=FauxUrlResponder(
                             [
                                 FauxUrlOpenResponse(data={'current_version': 'v1'}),
                                 FauxUrlOpenResponse(data={'results': [{'foo1': 11, 'foo2': 12}]},
                                                     url='blippyblopfakeurl'),
                             ]
                         ))

    patcher.start()
    api = rest_api.GalaxyAPI(gc)

    # do a call so that we run g_connect and _get_server_api_versions by side effect now
    api.lookup_repo_by_name('test-namespace', 'test-repo')

    # now unpatch
    patcher.stop()

    yield api


def test_galaxy_api_properties(galaxy_api):
    log.debug('api_server: %s', galaxy_api.api_server)
    log.debug('validate_certs: %s', galaxy_api.validate_certs)

    assert galaxy_api.api_server == 'https://galaxy-qa.ansible.com'
    assert galaxy_api.validate_certs is True


def test_galaxy_api_lookup_repo_by_name(mocker, galaxy_api):
    mocker.patch('ansible_galaxy.rest_api.open_url',
                 new=FauxUrlResponder(
                     [
                         FauxUrlOpenResponse(data={'stuff': [1, 2, 3],
                                                   'results': [{'foo1': 11, 'foo2': 12},
                                                               {'other_stuff': 'blip'}]
                                                   },
                                             url='blippyblopfakeurl'),
                     ]
                 ))

    namespace = 'alikins'
    name = 'role-awx'
    res = galaxy_api.lookup_repo_by_name(namespace, name)

    log.debug('res: %s', res)

    # FIXME: lookup_content_by_name only returns the first result
    assert isinstance(res, dict)
    assert 'foo1' in res


def test_galaxy_api_lookup_repo_by_name_empty_results(mocker, galaxy_api):
    mocker.patch('ansible_galaxy.rest_api.open_url',
                 new=FauxUrlResponder(
                     [
                         FauxUrlOpenResponse(data={'stuff': [1, 2, 3],
                                                   'results': [],
                                                   },
                                             url='blippyblopfakeurl'),
                     ]
                 ))

    namespace = 'alikins'
    name = 'role-awx'
    res = galaxy_api.lookup_repo_by_name(namespace, name)

    log.debug('res: %s', res)

    # If there are no results, we expect to get back an empty dict.
    # FIXME: should probably return the full list and let the app care what that means
    assert isinstance(res, dict)
    assert res == {}


def test_galaxy_api_lookup_repo_by_name_redirect_url(mocker, galaxy_api):
    mocker.patch('ansible_galaxy.rest_api.open_url',
                 new=FauxUrlResponder(
                     [
                         FauxUrlOpenResponse(data={'stuff': [1, 2, 3],
                                                   'results': [],
                                                   },
                                             url='blippyblopfakeurl',
                                             redirect_url='https://redirectedtothisurl/foo/blorp'),
                     ]
                 ))

    namespace = 'alikins'
    name = 'role-awx'
    res = galaxy_api.lookup_repo_by_name(namespace, name)

    log.debug('res: %s', res)

    # If there are no results, we expect to get back an empty dict.
    # FIXME: should probably return the full list and let the app care what that means
    assert isinstance(res, dict)
    assert res == {}


def test_galaxy_api_lookup_repo_by_name_500_json_not_dict(mocker, galaxy_api):
    mocker.patch('ansible_galaxy.rest_api.open_url',
                 side_effect=HTTPError(url='http://whatever',
                                       code=500,
                                       msg='Stuff broke.',
                                       hdrs={},
                                       fp=io.StringIO(initial_value=u'[]')))

    try:
        galaxy_api.lookup_repo_by_name('some-test-namespace', 'some-test-name')
    except exceptions.GalaxyClientError as e:
        log.exception(e)
        log.debug(e)
        return

    assert False, 'Excepted to get a HTTPError(code=500) here but did not.'


def test_galaxy_api_lookup_repo_by_name_500_json(mocker, galaxy_api):
    error_body_text = u'{"detail": "Stuff broke, 500 error but server response has valid json include the detail key"}'

    mocker.patch('ansible_galaxy.rest_api.open_url',
                 side_effect=HTTPError(url='http://whatever',
                                       code=500,
                                       msg='Stuff broke.',
                                       hdrs={},
                                       fp=io.StringIO(initial_value=error_body_text)))

    try:
        galaxy_api.lookup_repo_by_name('some-test-namespace', 'some-test-name')
    except exceptions.GalaxyClientError as e:
        log.exception(e)
        log.debug(e)
        return

    assert False, 'Excepted to get a GalaxyClientError here but did not.'


def test_galaxy_api_lookup_repo_by_name_SSLError(mocker, galaxy_api):
    mocker.patch('ansible_galaxy.rest_api.open_url',
                 side_effect=ssl.SSLError('ssl stuff broke... good luck and godspeed.'))

    try:
        galaxy_api.lookup_repo_by_name('some-test-namespace', 'some-test-name')
    except exceptions.GalaxyClientAPIConnectionError as e:
        log.exception(e)
        log.debug(e)

        return

    assert False, 'Excepted to get a GalaxyClientAPIConnectionError here but did not.'


def test_galaxy_api_fetch_content_related_500(mocker, galaxy_api):
    error_detail_text = u'{"detail": "Stuff broke, 500 error but server response has valid json include the detail key"}'
    mocker.patch('ansible_galaxy.rest_api.open_url',
                 side_effect=HTTPError(url='http://whatever',
                                       code=500,
                                       msg='Stuff broke.',
                                       hdrs={},
                                       fp=io.StringIO(initial_value=error_detail_text)))

    # FIXME: fetch_content_related has a catch-all exception handle that returns None for any exception (including http errors etc)
    try:
        res = galaxy_api.fetch_content_related('/api/v1/repositories/56683/content/')
        log.debug('res: %s', res)
    except exceptions.GalaxyClientError:
        return

    assert False, 'Excepted to get a GalaxyClientError here but did not.'


def test_galaxy_api_fetch_content_related(mocker, galaxy_api):
    url = '/api/v1/repositories/56683/content/'
    mocker.patch('ansible_galaxy.rest_api.open_url',
                 new=FauxUrlResponder(
                     [
                         FauxUrlOpenResponse(data={'next_link': '%s?page=2' % url,
                                                   'results': ['foo1', 'foo2']
                                                   },
                                             url='blippyblopfakeurl'),
                         FauxUrlOpenResponse(data={'results': ['foo3', 'foo4']
                                                   },
                                             url='blippyblopfakeurl'),
                     ]
                 ))

    res = galaxy_api.fetch_content_related('/api/v1/repositories/56683/content/')

    log.debug('res: %s', res)

    # TODO: use real-ish response data and verify it doesnt get munged
    assert isinstance(res, list)
    assert len(res) == 4
    assert 'foo1' in res
    assert 'foo4' in res
    assert all([isinstance(x, text_type) for x in res])


def test_galaxy_api_fetch_content_related_empty_results(mocker, galaxy_api):
    url = '/api/v1/repositories/56683/content/'
    mocker.patch('ansible_galaxy.rest_api.open_url',
                 new=FauxUrlResponder(
                     [
                         FauxUrlOpenResponse(data={'next_link': '%s?page=2' % url,
                                                   'results': []
                                                   },
                                             url='blippyblopfakeurl'),
                         FauxUrlOpenResponse(data={'results': [],
                                                   },
                                             url='blippyblopfakeurl'),
                     ]
                 ))

    res = galaxy_api.fetch_content_related('/api/v1/repositories/56683/content/')

    log.debug('res: %s', res)

    assert isinstance(res, list)
    assert len(res) == 0


def test_galaxy_api_fetch_content_related_no_results(mocker, galaxy_api):
    url = '/api/v1/repositories/56683/content/'
    mocker.patch('ansible_galaxy.rest_api.open_url',
                 new=FauxUrlResponder(
                     [
                         FauxUrlOpenResponse(data={'next_link': '%s?page=2' % url,
                                                   },
                                             url='blippyblopfakeurl'),
                         FauxUrlOpenResponse(data={},
                                             url='blippyblopfakeurl'),
                     ]
                 ))

    res = galaxy_api.fetch_content_related('/api/v1/repositories/56683/content/')

    log.debug('res: %s', res)

    assert isinstance(res, list)
    assert len(res) == 0


def test_user_agent():
    res = rest_api.user_agent()
    assert res.startswith('Mazer/%s' % ansible_galaxy.__version__)
    assert sys.platform in res
    assert 'python:' in res
    assert 'ansible_galaxy' in res
