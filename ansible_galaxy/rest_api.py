########################################################################
#
# (C) 2013, James Cammarata <jcammarata@ansible.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#
########################################################################

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import logging
import sys
import uuid

import requests

from six.moves.urllib.parse import quote as urlquote

from ansible_galaxy import __version__ as mazer_version
from ansible_galaxy import exceptions

log = logging.getLogger(__name__)
http_log = logging.getLogger('%s.(http).(general)' % __name__)
request_log = logging.getLogger('%s.(http).(request)' % __name__)
response_log = logging.getLogger('%s.(http).(response)' % __name__)

USER_AGENT_FORMAT = 'Mazer/{version} ({platform}; python:{py_major}.{py_minor}.{py_micro}) ansible_galaxy/{version}'


def user_agent():
    user_agent_data = {'version': mazer_version,
                       'platform': sys.platform,
                       'py_major': sys.version_info.major,
                       'py_minor': sys.version_info.minor,
                       'py_micro': sys.version_info.micro}
    return USER_AGENT_FORMAT.format(**user_agent_data)


def response_slug(response):
    # The slug we use to identify a request by method, url and request id
    # For ex, '"GET https://galaxy.ansible.com/api/v1/repositories" c48937f4e8e849828772c4a0ce0fd5ed'
    slug = '"%s %s" %s' % (response.request.method, response.url, response.request.headers['X-Request-Id'])
    return slug


def g_connect(method):
    ''' wrapper to lazily initialize connection info to galaxy '''

    def wrapped(self, *args, **kwargs):
        if not self.initialized:
            log.debug("Initial connection to galaxy_server: %s", self._api_server)

            server_version = self._get_server_api_version()

            if server_version not in self.SUPPORTED_VERSIONS:
                raise exceptions.GalaxyClientError("Unsupported Galaxy server API version: %s" % server_version)

            self.initialized = True
        return method(self, *args, **kwargs)
    return wrapped


class RestClient(object):
    '''http REST client

    Mostly wrapper around requests.Session and Session.request(), but with
    more logging.

    Also sets the mazer http user agent, and adds 'Request-ID' headers.
    '''

    def __init__(self, http_context=None):
        self.http_context = http_context or {}

        log.debug('http_context: %s', http_context)

        self.user_agent = user_agent()

        log.debug('User Agent: %s', self.user_agent)

        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})

        self.log = logging.getLogger(__name__ + '.' + self.__class__.__name__)

    @property
    def validate_certs(self):
        return not self.http_context['server']['ignore_certs']

    # TODO: raise an API/net specific exception?
    def mkrequest(self, url, args=None, headers=None, http_method=None):
        '''Make an REST-y http request to Galaxy APIs

        Requests that fail and raise exceptions are caught and
        either GalaxyClientAPIConnectionError or GalaxyRestAPIClientRequestError
        are raised. ie, mazer specific request error exceptions.

        Note: This only raises exceptions if the request fails (a connection failure,
              an SSL failure, DNS failure etc. If the server responds at all, this
              will not fail. Those cases are handled in GalaxyAPI.
        '''
        http_method = http_method or 'GET'

        request_headers = headers or {}
        request_id = uuid.uuid4().hex
        request_headers['X-Request-ID'] = request_id

        # The slug we use to identify a request by method, url and request id
        # For ex, '"GET https://galaxy.ansible.com/api/v1/repositories" c48937f4e8e849828772c4a0ce0fd5ed'
        pre_request_slug = '"%s %s" %s' % (http_method, url, request_id)

        # log the http request_slug with request_id to the main log and
        # to the http log, both at INFO level for now.
        http_log.info('%s', pre_request_slug)
        self.log.info('%s', pre_request_slug)

        # request_log.debug('%s headers=%s', pre_request_slug, request_headers)

        try:

            # Make the actual request
            resp = self.session.request(http_method, url, data=args, headers=request_headers,
                                        verify=self.validate_certs)

        except requests.exceptions.ConnectionError as connection_exc:
            self.log.debug('Connection exception on %s', pre_request_slug)
            self.log.exception("%s: %s %r", pre_request_slug, connection_exc, connection_exc)

            # TODO: The request.ConnectionError error messages are very knarly and obscure real
            #       cause of message (like a 'connection refused'). Try to improve these cases.
            raise exceptions.GalaxyClientAPIConnectionError(connection_exc,
                                                            response=connection_exc.response)

        except requests.exceptions.RequestException as request_exc:
            self.log.debug('Exception on %s', pre_request_slug)
            self.log.exception("%s: %s", pre_request_slug, request_exc)

            raise exceptions.GalaxyRestAPIClientRequestError(request_exc,
                                                             response=request_exc.response)

        # Log info about the request/response for debug
        log.debug('resp.request: %s', resp.request)
        # log.debug('resp.request.headers: %s', resp.request.headers)
        log.debug('resp: %s', resp)

        slug = response_slug(resp)

        response_log.info('%s http_status=%s reason=%s', slug, resp.status_code, resp.reason)
        response_log.debug('%s headers=%s', slug, resp.headers)

        if resp.history:
            for redirect in resp.history:
                log.debug('%s %s redirected -->  %s',
                          slug, redirect.url, redirect.headers['Location'])

        return resp

# main objects we will deal with
#
# Api
#     GET    /api/
# Collection
#     GET    /api/v2/collections/{namespace}/{name}
#     GET    /api/v2/collections/{id}
#    POST    /api/v2/collections/       (multiparm form post) "publish"
#
# CollectionVersion
#     GET     /api/v2/collections/{namespace}/{name}/versions/{version}
#
# CollectionCollectionVersion
#     GET    /api/v2/collections/{namespace}/{name}/versions/
#            ('versions_url' ref on Collection)
#


class GalaxyAPI(object):
    ''' This class is meant to be used as a API client for an Ansible Galaxy server '''

    SUPPORTED_VERSIONS = ['v1', 'v2']

    # FIXME: just pass in server_url
    def __init__(self, galaxy_context):
        self.galaxy_context = galaxy_context

        log.debug('Using galaxy server URL %s with ignore_certs=%s', galaxy_context.server['url'], galaxy_context.server['ignore_certs'])

        self.log = logging.getLogger(__name__ + '.' + self.__class__.__name__)

        # set the API server
        self._api_server = galaxy_context.server['url']

        self.rest_client = RestClient(http_context={'server': galaxy_context.server})
        # self.log.debug('Validate TLS certificates for %s: %s', self._api_server, self._validate_certs)

        # This is set to true by the g_connect wrapper once there is there has been a server api check
        self.initialized = False

    @property
    def api_server(self):
        return self._api_server

    @property
    def base_api_url(self):
        return '%s/api' % self._api_server

    def _get_server_api_version(self):
        """
        Fetches the Galaxy API current version to ensure
        the API server is up and reachable.
        """
        url = '%s/api/' % self._api_server

        # Call without the @g_connect wrapper to avoid recursion
        data = self._get_object(href=url)

        if 'current_version' not in data:
            # The Galaxy API info at http://bogus.invalid:9443/api/ is missing the required 'current_version' field and the API version could not be determined.
            error_msg = "The Galaxy API version could not be determined. The required 'current_version' field is missing from info at %s" % url

            raise exceptions.GalaxyClientError(error_msg)

        self.log.debug('Server API version of URL %s is "%s"', url, data['current_version'])

        return data['current_version']

    def paginate(self, data):
        """
        Fetch the list of related items for the given role.
        The url comes from the 'related' field of the role.
        """

        # This is not an object that could have paging data
        if not isinstance(data, dict):
            return data

        # No results list, so not paged
        if 'results' not in data:
            return data

        if 'next' not in data and 'count' not in data:
            return data

        results = data['results']

        done = (data.get('next', None) is None)

        while not done:
            next_url = data['next']

            log.debug('next_url: %s', next_url)

            # Basic get_object() but sans automatic paging
            resp = self.rest_client.mkrequest(url=next_url, http_method='GET')
            next_data = self.handle_response(resp)

            # can assume all the rest of the links will also be 'page' dicts
            # if no results, default to a empty list
            results += next_data.get('results', [])

            done = (next_data.get('next', None) is None)

        return results

    @g_connect
    def get_collection_detail(self, namespace, name):
        namespace = urlquote(namespace)
        name = urlquote(name)
        url = "%s%s" % (self.base_api_url,
                        '/v2/collections/{namespace}/{name}'.format(namespace=namespace, name=name))

        data = self.get_object(href=url)
        return data

    def handle_response(self, resp):
        slug = response_slug(resp)

        try:
            data = resp.json()
            # debug log a json version of the data that was created from the response
            # self.log.debug('%s data:\n%s', slug, json.dumps(data, indent=2))
        except ValueError as e:
            log.exception(e)
            data = None

        # Convert/map/raise any errors returned from galaxy api into exceptions

        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as http_exc:
            self.log.debug('Exception on %s', slug)
            self.log.exception("%s: %s", slug, http_exc)

            # http_log.error('%s data from server error response:\n%s', slug, http_exc.response)

            error_data = None

            if http_exc.response is not None:
                try:
                    error_data = http_exc.response.json()
                except (ValueError, KeyError, TypeError) as detail_parse_exc:
                    self.log.exception("%s: %s", slug, detail_parse_exc)
                    self.log.warning('Unable to parse error detail from response for request: %s response:  %s', slug, detail_parse_exc)

                    # Got an http response, but it wasn't valid json, so not an exception from the web app
                    raise exceptions.GalaxyRestServerError(http_exc,
                                                           response=http_exc.response)

            # TODO: great place to be able to use 'raise from'
            raise exceptions.GalaxyRestAPIError(http_exc,
                                                response=http_exc.response,
                                                error_data=error_data)

        return data

    def post_multipart_form(self, url, form, headers=None):
        form_buffer = form.get_binary().getvalue()

        headers['Content-type'] = form.get_content_type()
        headers['Content-length'] = str(len(form_buffer))

        resp = self.rest_client.mkrequest(url=url,
                                          http_method='POST',
                                          args=form_buffer,
                                          headers=headers)

        return self.handle_response(resp)

    # _get_object is not decorated with @g_connect, so we can call it
    # directly from _get_server_api_version() without recursion
    def _get_object(self, href=None):
        '''Get a full url and return deserialized results'''

        # responses = self.rest_client.mkrequest():
        # return self.handle_responses(responses)
        resp = self.rest_client.mkrequest(url=href, http_method='GET')

        data = self.handle_response(resp)

        # determine if the data is paginated and if so, page it and accumulate results
        return self.paginate(data)

    @g_connect
    def get_object(self, href=None):
        '''Get a full url and return deserialized results'''
        return self._get_object(href=href)

    @g_connect
    def publish_file(self, form, publish_api_key):
        # TODO: at somepoint, get the publish url from api
        collection_url_ver = 'v2'
        url = '%s/%s/collections/' % (self.base_api_url, collection_url_ver)

        request_headers = {}

        # TODO: create or use a request.Auth impl
        if publish_api_key:
            request_headers['Authorization'] = 'Token %s' % publish_api_key

        # FIXME: too tightly coupled
        artifact_path = form.files[0][1]

        try:
            # TODO: pass in a file-like object and use stream=True

            data = self.post_multipart_form(url,
                                            form=form,
                                            headers=request_headers)

            return data
        except exceptions.GalaxyRestAPIError as exc:
            log.exception(exc)

            error_msg = exc.message

            raise exceptions.GalaxyPublishError(
                error_msg,
                archive_path=artifact_path,
                url=url
            )
