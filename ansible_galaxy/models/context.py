########################################################################
#
# (C) 2015, Brian Coca <bcoca@ansible.com>
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
''' This manages remote shared Ansible objects, mainly roles'''

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import logging
import os

log = logging.getLogger(__name__)


class GalaxyContext(object):
    ''' Keeps global galaxy info '''

    def __init__(self, content_roots=None, servers=None):

        log.debug('content_roots: %s', content_roots)
        log.debug('servers: %s', servers)

        self.servers = servers or []
        self.content_roots = content_roots or []

        # default_content_paths = [os.path.expanduser(p) for p in defaults.DEFAULT_CONTENT_PATH]
        # content_paths = getattr(self.options, 'content_path', [])

    @property
    def server_url(self):
        if not self.servers:
            return None
        # Default to first server in the list
        return self.servers[0]['url']

    @property
    def ignore_certs(self):
        if not self.servers:
            return None
        # Default to first server in the list
        return self.servers[0]['ignore_certs']

    @property
    def content_path(self):
        if not self.content_roots:
            return None
        # Default to first content_root in the list
        return self.content_roots[0]

    @classmethod
    def from_config_and_options(cls, config, options):
        '''Create a GalaxyContext based on config data and cli options'''
        servers_from_config = config.get('servers', [])
        content_roots_from_config = config.get('content_roots', [])

        # default_content_paths = [os.path.expanduser(p) for p in defaults.DEFAULT_CONTENT_PATH]
        _servers = []

        # FIXME(alikins): changed my mind, should move this back to cli/ code
        if options:
            if getattr(options, 'content_path', None):
                _option_content_paths = []

                for content_path in options.content_path:
                    _option_content_paths.append(content_path)

            # If someone provides a --roles-path at the command line, we assume this is
            # for use with a legacy role and we want to maintain backwards compat
            if getattr(options, 'roles_path', None):
                log.warn('Assuming content is of type "role" since --role-path was used')
                _option_role_paths = []
                for role_path in options.roles_path:
                    _option_role_paths.append(role_path)

            # if a server was provided via cli, prepend it to the server list
            if getattr(options, 'server_url', None):
                cli_server = {'url': options.server_url}

                ignore_certs = options.ignore_certs or False
                cli_server['ignore_certs'] = ignore_certs

                _servers = [cli_server]

        # list of dicts with 'name' and 'content_path' items
        # cli --content-paths is hight priority, then --role-path, then configured content-paths
        raw_content_roots = _option_content_paths + _option_role_paths + content_roots_from_config[:]

        log.debug('raw_content_roots: %s', raw_content_roots)
        content_roots = [os.path.expanduser(p) for p in raw_content_roots]

        # list of dicts of url, ignore_certs, token keys
        servers = _servers + servers_from_config[:]

        inst = cls(content_roots=content_roots, servers=servers)

        return inst

    def __repr__(self):
        return 'GalaxyContext(content_roots=%s, servers=%s)' % \
            (self.content_roots, self.servers)

    # def add_role(self, role):
    #    self.roles[role.name] = role

    # def remove_role(self, role_name):
    #    del self.roles[role_name]

    # def add_content(self, content):
    #    self.content[content.name] = content

    # def remove_content(self, content_name):
    #     del self.content[content_name]
