########################################################################
#
# (C) 2015, Brian Coca <bcoca@ansible.com>
# (C) 2018, Adam Miller <admiller@redhat.com>
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

import datetime
import logging
import os
from shutil import rmtree
import pprint

import attr

from ansible_galaxy import exceptions
from ansible_galaxy import archive
from ansible_galaxy import content_archive
from ansible_galaxy import install_info
from ansible_galaxy import role_metadata
from ansible_galaxy import display
from ansible_galaxy.models.content import CONTENT_TYPES
from ansible_galaxy.models.content import CONTENT_TYPE_DIR_MAP
from ansible_galaxy.models import content
from ansible_galaxy.models.install_info import InstallInfo


log = logging.getLogger(__name__)

# has a GalaxyContentMeta FIXME: rename back to GalaxyContentData
# FIXME: erk, and a metadata (ie, ansible-galaxy.yml)
#
# can provide a InstallInfo


# TODO: add InstalledContent
#       get rid of GalaxyContent.metadata / GalaxyContent.install_info
#       for Instal\bledContent add a from_install_info() to build it from file at creation
#        get rid of deferred install_info load? or maybe a special InstallInfo instance?
#       ditto for 'self.metadata'
#
# FIXME: really just three methods here, install, remove, fetch. install -> save, fetch -> load
#       remove -> delete
class GalaxyContent(object):

    SUPPORTED_SCMS = set(['git', 'hg'])
    META_INSTALL = os.path.join('meta', '.galaxy_install_info')
    ROLE_DIRS = ('defaults', 'files', 'handlers', 'meta', 'tasks', 'templates', 'vars', 'tests')
    NO_META = ('module', 'strategy_plugin')
    REQUIRES_META_MAIN = ('role')

    # FIXME(alikins): Not a fan of vars/args with names like 'type', but leave it for now
    def __init__(self,
                 galaxy,
                 name,
                 src=None,
                 version=None,
                 scm=None,
                 path=None,
                 content_type=None,
                 content_meta=None,
                 content_spec=None,
                 sub_name=None,
                 namespace=None,
                 # metadata is the info in roles meta/main.yml for ex
                 metadata=None,
                 # install_info is info in meta/.galaxy_install_info for installed content packages
                 install_info=None,
                 display_callback=None):
        """
        The GalaxyContent type is meant to supercede the old GalaxyRole type,
        supporting all Galaxy Content Types as per the Galaxy Repository Metadata
        specification.

        The "content_type" is default to "role" in order to maintain backward
        compatibility as a drop-in replacement for GalaxyRole

        :param galaxy: Galaxy object from ansible.galaxy
        :param name: str, name of Galaxy Content desired
        :kw src: str, source uri
        :kw version: str, version required/requested
        :kw scm: str, scm type
        :kw path: str, local path to Galaxy Content
        :kw content_type: str, Galaxy Content type
        """

        # what we are installing 'as', or what content subset we want to install
        self.content_install_type = 'all'

        if not content_type:
            content_type = 'role'

        self._content_type = content_type
        self._metadata = metadata

        self._install_info = install_info

        self.log = logging.getLogger(__name__ + '.' + self.__class__.__name__)
        self.log.debug('init name=%s, namespace=%s, path=%s', name, namespace, path)

        self.display_callback = display_callback or display.display_callback

        # self.options = galaxy.options
        self.galaxy = galaxy

        # FIXME: validate_certs is an option for two different things,
        #        the connection to the galaxy_server (eg, galaxy.ansible.com)
        #        and to where archives are downloaded (eg, github)
        self._validate_certs = not galaxy.server['ignore_certs']

        # FIXME
        self.sub_name = sub_name

        self.content_spec = content_spec

        # self.galaxy.content_roots['default']['content_path']
        primary_galaxy_content_path = self.galaxy.content_path

        # If the content requires a meta/main.yml file ala roles
        # requires_meta_main = False
        # if content_type in self.REQUIRES_META_MAIN:
        #    requires_meta_main = True

        self.content_meta = content_meta or \
            content.GalaxyContentMeta(namespace=namespace,
                                      name=name,
                                      version=version,
                                      src=src,
                                      scm=scm,
                                      content_type=self._content_type,
                                      content_dir=CONTENT_TYPE_DIR_MAP.get(content_type, None),
                                      path=primary_galaxy_content_path)

        # TODO: factory? metaclass?
        if content_type not in CONTENT_TYPES and content_type != "all":
            raise exceptions.GalaxyClientError("%s is not a valid Galaxy Content Type" % content_type)

        # Set original path, needed to determine what action to take in order to
        # maintain backwards compat with legacy roles
        self._orig_path = path

        # TODO: state machine for find->fetch->install
        # data from fetch.find() where we find, discover, and resolve info about the content
        #  (ie, via asking the galaxy api)
        self._find_results = None

    def __not_repr__(self):
        """
        Returns "content_name (version) content_type" if version is not null
        Returns "content_name content_type" otherwise
        """
        if self.version:
            return "%s (%s) %s" % (self.content_meta.name, self.version, self.content_type)
        else:
            return "%s %s" % (self.content_meta.name, self.content_type)

    def __eq__(self, other):
        return self.content_meta.name == other.content_meta.name

    # FIXME: update calling code instead?
    @property
    def name(self):
        return self.content_meta.name

    @property
    def label(self):
        return self.content_meta.label

    @property
    def version(self):
        return self.content_meta.version

    @property
    def src(self):
        return self.content_meta.src

    @property
    def scm(self):
        return self.content_meta.scm

    @property
    def content_dir(self):
        return self.content_meta.content_dir

    @property
    def content_type(self):
        return self._content_type

    @property
    def path(self):
        return self.content_meta.path

    @property
    def metadata(self):
        return self._metadata

    @property
    def install_info(self):
        return self._install_info

    def remove(self):
        raise exceptions.GalaxyError('Calling remove() on a GalaxyContent (not InstalledGalaxyContent) doesnt mean anything')

    # TODO: property of GalaxyContentMeta ?
    @property
    def spec(self):
        """
        Returns content spec info
        {
           'scm': 'git',
           'src': 'http://git.example.com/repos/repo.git',
           'version': 'v1.0',
           'name': 'repo'
        }
        """
        return dict(scm=self.scm, src=self.src, version=self.version, name=self.content_meta.name)


# TODO/FIXME: revist a Content base class
class InstalledContent(GalaxyContent):
    @property
    def metadata_path(self):
        return os.path.join(self.path, self.content_meta.namespace, self.content_meta.name,
                            self.content_meta.content_dir, self.content_meta.name, content_archive.META_MAIN)

    @property
    def metadata(self):
        """
        Returns role metadata for type role, errors otherwise
        """
        log.debug('metadata prop')
        if self.content_meta.content_type not in ('role', 'all'):
            log.debug('content_type not role %s', self.content_meta.content_type)
            return {}

        # if self._metadata is not None:
        if self._metadata is None:
            self._metadata = role_metadata.load_from_filename(self.metadata_path,
                                                              role_name=self.content_meta.name)

        return self._metadata

    @property
    def install_info_path(self):
        # TODO: once this class is mostly immutable, this wont need to be a property
        return os.path.join(self.path, self.content_meta.namespace, self.content_meta.name,
                            self.content_meta.content_dir, self.content_meta.name, self.META_INSTALL)

    # TODO: class/module for InstallInfo
    @property
    def install_info(self):
        """
        Returns Galaxy Content install info
        """
        # FIXME: Do we want to have this for galaxy content?
        if self._install_info is None:
            self._install_info = install_info.load_from_filename(self.install_info_path)
        return self._install_info

    def remove(self):
        """
        Removes the specified content from the content path.
        There is a sanity check to make sure there's a meta/main.yml or
        ansible-galaxy.yml file at this path so the user doesn't blow away
        random directories.
        """
        log.debug('remove content_type: %s', self.content_type)
        log.debug('remove metadata: %s', self.metadata)
        log.debug('remove path: %s', self.path)

        # FIXME - not yet implemented for non-role types
        if self.content_type == "role":
            if self.metadata:
                try:
                    rmtree(self.path)
                    return True
                except Exception as e:
                    log.warn('unable to rmtree for path=%s', self.path)
                    log.exception(e)

        else:
            raise exceptions.GalaxyClientError("Removing Galaxy Content not yet implemented")

        return False
