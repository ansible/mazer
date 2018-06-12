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
from six.moves.urllib.error import HTTPError
from six.moves.urllib.parse import quote as urlquote, urlencode
import socket
import ssl

from ansible_galaxy import exceptions
from ansible_galaxy.utils.text import to_native, to_text

# FIXME: would be nice to just use requests, or better, some async https client
from ansible_galaxy.flat_rest_api.urls import open_url

log = logging.getLogger(__name__)
http_log = logging.getLogger('%s.(http)' % __name__)
request_log = logging.getLogger('%s.(http).(request)' % __name__)
response_log = logging.getLogger('%s.(http).(response)' % __name__)


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
            log.debug("Base API: %s", self.baseurl)
            self.initialized = True
        return method(self, *args, **kwargs)
    return wrapped


class GalaxyAPI(object):
    ''' This class is meant to be used as a API client for an Ansible Galaxy server '''

    SUPPORTED_VERSIONS = ['v1']

    # FIXME: just pass in server_url
    def __init__(self, galaxy):
        self.galaxy = galaxy
        log.debug('galaxy: %s', galaxy)
        log.debug('galaxy.server: %s', galaxy.server)
        self._validate_certs = not galaxy.server['ignore_certs']
        self.baseurl = None
        self.version = None
        self.initialized = False
        self.log = logging.getLogger(__name__ + '.' + self.__class__.__name__)

        # set the API server
        self._api_server = galaxy.server['url']
        self.log.debug('Validate TLS certificates for %s: %s', self._api_server, self._validate_certs)

    # TODO: raise an API/net specific exception?
    @g_connect
    def __call_galaxy(self, url, args=None, headers=None, method=None):
        headers = headers or {}

        try:
            http_log.info('%s %s', method, url)
            request_log.debug('%s %s args=%s', method, url, args)
            request_log.debug('%s %s headers=%s', method, url, headers)

            resp = open_url(url, data=args, validate_certs=self._validate_certs,
                            headers=headers, method=method,
                            timeout=20)

            http_log.info('%s %s http_status=%s', method, url, resp.getcode())

            final_url = resp.geturl()
            if final_url != url:
                http_log.debug('%s %s Redirected to: %s', method, url, resp.geturl())

            resp_info = resp.info()
            response_log.debug('%s %s info:\n%s', method, url, resp_info)

            # FIXME: making the request and loading the response should be sep try/except blocks
            response_body = to_text(resp.read(), errors='surrogate_or_strict')

            # debug log the raw response body
            response_log.debug('%s %s response body:\n%s', method, url, response_body)

            data = json.loads(response_body)

            # debug log a json version of the data that was created from the response
            response_log.debug('%s %s data:\n%s', method, url, json.dumps(data, indent=2))
        except HTTPError as e:
            self.log.debug('Exception on %s %s', method, url)
            self.log.exception(e)

            # FIXME: probably need a try/except here if the response body isnt json which
            #        can happen if a proxy mangles the response
            res = json.loads(to_text(e.fp.read(), errors='surrogate_or_strict'))

            http_log.error('%s %s data from server error response:\n%s', method, url, res)

            raise exceptions.GalaxyClientError(res['detail'])
        except (ssl.SSLError, socket.error) as e:
            self.log.debug('Connection error to Galaxy API for request "%s %s": %s', method, url, e)
            self.log.exception(e)
            raise exceptions.GalaxyClientAPIConnectionError('Connection error to Galaxy API for request "%s %s": %s' % (method, url, e))

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
        self.log.debug('get_server_api url=%s', url)

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

        return data['current_version']

    @g_connect
    def lookup_repo_by_name(self, namespace, name):
        self.log.debug('user_name=%s', namespace)
        self.log.debug('name=%s', name)
        namespace = urlquote(namespace)
        name = urlquote(name)
        url = '%s/repositories/?name=%s&provider_namespace__namespace__name=%s' % (self.baseurl, name, namespace)
        data = self.__call_galaxy(url)
        if len(data["results"]) != 0:
            return data["results"][0]
        return None

    @g_connect
    def lookup_content_by_name(self, namespace, repo_name, content_name, content_type=None, notify=True):
        self.log.debug('namespace=%s', namespace)
        self.log.debug('repo_name=%s', repo_name)
        self.log.debug('content_name=%s', content_name)
        self.log.debug('content_type=%s', content_type)
        self.log.debug('notify=%s', notify)

        content_name = urlquote(content_name)
        repo_name = urlquote(repo_name)

        if notify:
            self.log.info("- downloading content '%s', type '%s',repo_name '%s'  owned by %s", content_name, content_type, repo_name, namespace)

        url = '%s/content/?name=%s&namespace__name=%s' % (self.baseurl, content_name, namespace)
        data = self.__call_galaxy(url)
        if len(data["results"]) != 0:
            return data["results"][0]
        return None

    @g_connect
    def lookup_role_by_name(self, role_name, notify=True):
        """
        Find a role by name.
        """
        self.log.debug('role_name=%s', role_name)
        role_name = urlquote(role_name)

        try:
            parts = role_name.split(".")
            user_name = ".".join(parts[0:-1])
            role_name = parts[-1]
            if notify:
                self.log.info("- downloading role '%s', owned by %s", role_name, user_name)
        except Exception as e:
            self.log.exception(e)
            raise exceptions.GalaxyClientError("Invalid role name (%s). Specify role as format: username.rolename" % role_name)

        url = '%s/roles/?owner__username=%s&name=%s' % (self.baseurl, user_name, role_name)
        data = self.__call_galaxy(url)
        if len(data["results"]) != 0:
            return data["results"][0]
        return None

    @g_connect
    def fetch_content_related(self, related_url):
        """
        Fetch the list of related items for the given role.
        The url comes from the 'related' field of the role.
        """
        self.log.debug('related_url=%s', related_url)

        try:
            url = '%s%s?page_size=50' % (self._api_server, related_url)
            data = self.__call_galaxy(url)
            results = data.get('results', None)
            if results is None:
                # not a results list, just return the item
                return data

            done = (data.get('next_link', None) is None)
            while not done:
                url = '%s%s' % (self._api_server, data['next_link'])
                data = self.__call_galaxy(url)
                results += data['results']
                done = (data.get('next_link', None) is None)
            return results
        except Exception as e:
            self.log.exception(e)
            return None

    @g_connect
    def get_list(self, what):
        """
        Fetch the list of items specified.
        """
        self.log.debug('what=%s', what)

        try:
            url = '%s/%s/?page_size' % (self.baseurl, what)
            data = self.__call_galaxy(url)
            if "results" in data:
                results = data['results']
            else:
                results = data
            done = True
            if "next" in data:
                done = (data.get('next_link', None) is None)
            while not done:
                url = '%s%s' % (self._api_server, data['next_link'])
                data = self.__call_galaxy(url)
                results += data['results']
                done = (data.get('next_link', None) is None)
            return results
        except Exception as error:
            self.log.exception(error)
            raise exceptions.GalaxyClientError("Failed to download the %s list: %s" % (what, str(error)))

    @g_connect
    def add_secret(self, source, github_user, github_repo, secret):
        url = "%s/notification_secrets/" % self.baseurl
        args = urlencode({
            "source": source,
            "github_user": github_user,
            "github_repo": github_repo,
            "secret": secret
        })
        data = self.__call_galaxy(url, args=args)
        return data
