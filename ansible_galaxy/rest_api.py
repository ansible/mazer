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
import json
import sys
import uuid

from six.moves.urllib.error import HTTPError
from six.moves.urllib.parse import quote as urlquote
import socket
import ssl

from ansible_galaxy import __version__ as mazer_version
from ansible_galaxy import exceptions
from ansible_galaxy.utils.text import to_native, to_text

# FIXME: would be nice to just use requests, or better, some async https client
from ansible_galaxy.flat_rest_api.urls import open_url

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


def g_connect(method):
    ''' wrapper to lazily initialize connection info to galaxy '''
    def wrapped(self, *args, **kwargs):
        if not self.initialized:
            log.debug("Initial connection to galaxy_server: %s", self._api_server)

            server_version = self._get_server_api_version()

            if server_version not in self.SUPPORTED_VERSIONS:
                raise exceptions.GalaxyClientError("Unsupported Galaxy server API version: %s" % server_version)

            self.baseurl = '%s/api/%s' % (self._api_server, server_version)
            self.version = server_version  # for future use

            # log.debug("Base API: %s", self.baseurl)

            self.initialized = True
        return method(self, *args, **kwargs)
    return wrapped


class GalaxyAPI(object):
    ''' This class is meant to be used as a API client for an Ansible Galaxy server '''

    SUPPORTED_VERSIONS = ['v1']

    # FIXME: just pass in server_url
    def __init__(self, galaxy):
        self.galaxy = galaxy

        # log.debug('galaxy: %s', galaxy)
        log.debug('Using galaxy server URL %s with ignore_certs=%s', galaxy.server['url'], galaxy.server['ignore_certs'])

        self._validate_certs = not galaxy.server['ignore_certs']
        self.baseurl = None
        self.version = None
        self.initialized = False
        self.log = logging.getLogger(__name__ + '.' + self.__class__.__name__)

        # set the API server
        self._api_server = galaxy.server['url']

        # self.log.debug('Validate TLS certificates for %s: %s', self._api_server, self._validate_certs)

        self.user_agent = user_agent()
        log.debug('User Agent: %s', self.user_agent)

    # TODO: raise an API/net specific exception?
    @g_connect
    def __call_galaxy(self, url, args=None, headers=None, http_method=None):
        http_method = http_method or 'GET'
        headers = headers or {}
        request_id = uuid.uuid4().hex
        headers['X-Request-ID'] = request_id

        # The slug we use to identify a request by method, url and request id
        # For ex, '"GET https://galaxy.ansible.com/api/v1/repositories" c48937f4e8e849828772c4a0ce0fd5ed'
        request_slug = '"%s %s" %s' % (http_method, url, request_id)

        try:
            # log the http request_slug with request_id to the main log and
            # to the http log, both at INFO level for now.
            http_log.info('%s', request_slug)
            self.log.info('%s', request_slug)

            request_log.debug('%s args=%s', request_slug, args)
            request_log.debug('%s headers=%s', request_slug, headers)

            resp = open_url(url, data=args, validate_certs=self._validate_certs,
                            headers=headers, method=http_method,
                            http_agent=self.user_agent,
                            timeout=20)

            response_log.info('%s http_status=%s', request_slug, resp.getcode())

            final_url = resp.geturl()
            if final_url != url:
                request_log.debug('%s Redirected to: %s', request_slug, resp.geturl())

            resp_info = resp.info()
            response_log.debug('%s info:\n%s', request_slug, resp_info)

            # FIXME: making the request and loading the response should be sep try/except blocks
            response_body = to_text(resp.read(), errors='surrogate_or_strict')

            # debug log the raw response body
            response_log.debug('%s response body:\n%s', request_slug, response_body)

            data = json.loads(response_body)

            # debug log a json version of the data that was created from the response
            response_log.debug('%s data:\n%s', request_slug, json.dumps(data, indent=2))
        except HTTPError as http_exc:
            self.log.debug('Exception on %s', request_slug)
            self.log.exception("%s: %s", request_slug, http_exc)

            # FIXME: probably need a try/except here if the response body isnt json which
            #        can happen if a proxy mangles the response
            res = json.loads(to_text(http_exc.fp.read(), errors='surrogate_or_strict'))

            http_log.error('%s data from server error response:\n%s', request_slug, res)

            try:
                error_msg = 'HTTP error on request %s: %s' % (request_slug, res['detail'])
                raise exceptions.GalaxyClientError(error_msg)
            except (KeyError, TypeError) as detail_parse_exc:
                self.log.exception("%s: %s", request_slug, detail_parse_exc)
                self.log.warning('Unable to parse error detail from response for request: %s response:  %s', request_slug, detail_parse_exc)

            # TODO: great place to be able to use 'raise from'
            # FIXME: this needs to be tweaked so the
            raise exceptions.GalaxyClientError(http_exc)
        except (ssl.SSLError, socket.error) as e:
            self.log.debug('Connection error to Galaxy API for request %s: %s', request_slug, e)
            self.log.exception("%s: %s", request_slug, e)
            raise exceptions.GalaxyClientAPIConnectionError('Connection error to Galaxy API for request %s: %s' % (request_slug, e))

        return data

    @property
    def api_server(self):
        return self._api_server

    @property
    def validate_certs(self):
        return self._validate_certs

    def _get_server_api_version(self):
        """
        Fetches the Galaxy API current version to ensure
        the API server is up and reachable.
        """
        url = '%s/api/' % self._api_server

        try:
            return_data = open_url(url, validate_certs=self._validate_certs)
        except Exception as e:
            raise exceptions.GalaxyClientError("Failed to get data from the API server (%s): %s " % (url, to_native(e)))

        try:
            data = json.loads(to_text(return_data.read(), errors='surrogate_or_strict'))
        except Exception as e:
            raise exceptions.GalaxyClientError("Could not process data from the API server (%s): %s " % (url, to_native(e)))

        if 'current_version' not in data:
            raise exceptions.GalaxyClientError("missing required 'current_version' from server response (%s)" % url)

        self.log.debug('Server API version of URL %s is "%s"', url, data['current_version'])
        return data['current_version']

    @g_connect
    def lookup_repo_by_name(self, namespace, name):
        namespace = urlquote(namespace)
        name = urlquote(name)
        url = '%s/repositories/?name=%s&provider_namespace__namespace__name=%s' % (self.baseurl, name, namespace)
        data = self.__call_galaxy(url, http_method='GET')
        if data["results"]:
            return data["results"][0]
        return {}

    @g_connect
    def fetch_content_related(self, related_url):
        """
        Fetch the list of related items for the given role.
        The url comes from the 'related' field of the role.
        """
        self.log.debug('related_url=%s', related_url)

        # try:
        url = '%s%s?page_size=50' % (self._api_server, related_url)

        # can raise a GalaxyClientError
        data = self.__call_galaxy(url, http_method='GET')

        # empty list for return value if there are no results
        results = data.get('results', [])

        # TODO: generalize the pagination support
        # check for paginated results
        done = (data.get('next_link', None) is None)

        while not done:
            url = '%s%s' % (self._api_server, data['next_link'])
            data = self.__call_galaxy(url, http_method='GET')

            # if no results, default to a empty list
            results += data.get('results', [])

            done = (data.get('next_link', None) is None)

        return results
