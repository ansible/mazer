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

import os

from ansible_galaxy.config import defaults


class GalaxyContext(object):
    ''' Keeps global galaxy info '''

    def __init__(self, options):

        self.options = options
        # self.options.roles_path needs to be a list and will be by default
        roles_path = getattr(self.options, 'roles_path', [])

        # cli option handling is responsible for making roles_path a list
        self.roles_paths = roles_path

        default_content_paths = [os.path.expanduser(p) for p in defaults.DEFAULT_CONTENT_PATH]
        content_paths = getattr(self.options, 'content_path', [])

        self.content_paths = content_paths + default_content_paths

        self.roles = {}

        # FIXME self.content will eventually replace self.roles when we're ready
        # to deprecate
        self.content = {}

        # load data path for resource usage
        # FIXME/TODO(akl): Need better way to find this other than __file__
        # this_dir, this_filename = os.path.split(__file__)
        # type_path = getattr(self.options, 'role_type', "default")
        # self.DATA_PATH = os.path.join(this_dir, 'data', type_path)

    def __repr__(self):
        return 'GalaxyContext(roles_path=%s, content_paths=%s, roles=%s, options=%s)' % \
            (self.roles_paths, self.content_paths, self.roles, self.options)

    def add_role(self, role):
        self.roles[role.name] = role

    def remove_role(self, role_name):
        del self.roles[role_name]

    def add_content(self, content):
        self.content[content.name] = content

    def remove_content(self, content_name):
        del self.content[content_name]
