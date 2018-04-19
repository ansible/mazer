########################################################################
#
# (C) 2015, Chris Houseknecht <chouse@ansible.com>
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

import getpass
import json
import logging

import six
from six.moves.urllib.error import HTTPError

from ansible_galaxy import exceptions
from ansible_galaxy.flat_rest_api.urls import open_url


log = logging.getLogger(__name__)


class GalaxyLogin(object):
    ''' Class to handle authenticating user with Galaxy API prior to performing CUD operations '''

    GITHUB_AUTH = 'https://api.github.com/authorizations'

    def __init__(self, galaxy, github_token=None):
        self.galaxy = galaxy
        self.github_username = None
        self.github_password = None

        self.log = logging.getLogger(__name__ + '.' + self.__class__.__name__)

        if github_token is None:
            self.get_credentials()

    def get_credentials(self):
        # FIXME(alikins) replace with a display callback
        print(u'\n\n' + "We need your " + 'Github login' +
              " to identify you.")
        print("This information will " + "not be sent to Galaxy" +
              ", only to " + "api.github.com.")
        print("The password will not be displayed." + u'\n\n')
        print("Use " + "--github-token" +
              " if you do not want to enter your password." + u'\n\n')

        try:
            self.github_username = six.input("Github Username: ")
        except:
            pass

        try:
            self.github_password = getpass.getpass("Password for %s: " % self.github_username)
        except:
            pass

        if not self.github_username or not self.github_password:
            raise exceptions.GalaxyClientError("Invalid Github credentials. Username and password are required.")

    def remove_github_token(self):
        '''
        If for some reason an ansible-galaxy token was left from a prior login, remove it. We cannot
        retrieve the token after creation, so we are forced to create a new one.
        '''
        try:
            tokens = json.load(open_url(self.GITHUB_AUTH, url_username=self.github_username,
                               url_password=self.github_password, force_basic_auth=True,))
        except HTTPError as e:
            res = json.load(e)
            raise exceptions.GalaxyClientError(res['message'])

        for token in tokens:
            if token['note'] == 'ansible-galaxy login':
                self.log.debug('removing token: %s', token['token_last_eight'])
                try:
                    open_url('https://api.github.com/authorizations/%d' % token['id'], url_username=self.github_username,
                             url_password=self.github_password, method='DELETE', force_basic_auth=True)
                except HTTPError as e:
                    self.log.exception(e)
                    res = json.load(e)
                    raise exceptions.GalaxyClientError(res['message'])

    def create_github_token(self):
        '''
        Create a personal authorization token with a note of 'ansible-galaxy login'
        '''
        self.remove_github_token()
        args = json.dumps({"scopes": ["public_repo"], "note": "ansible-galaxy login"})
        try:
            data = json.load(open_url(self.GITHUB_AUTH, url_username=self.github_username,
                             url_password=self.github_password, force_basic_auth=True, data=args))
        except HTTPError as e:
            self.log.exception(e)
            res = json.load(e)
            raise exceptions.GalaxyClientError(res['message'])
        return data['token']
