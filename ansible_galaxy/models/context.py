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

log = logging.getLogger(__name__)


class GalaxyContext(object):
    ''' Keeps global galaxy info '''

    def __init__(self, collections_path=None, server=None):
        self.server = server or {'url': None,
                                 'ignore_certs': False}
        self.collections_path = collections_path

    def __repr__(self):
        return 'GalaxyContext(collections_path=%s, server=%s)' % \
            (self.collections_path, self.server)
