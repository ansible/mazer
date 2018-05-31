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
import pprint
from shutil import rmtree
import tarfile
import yaml

from ansible_galaxy import exceptions
from ansible_galaxy import archive
from ansible_galaxy.content_repo_galaxy_metadata import install_from_galaxy_metadata
from ansible_galaxy import display
from ansible_galaxy.fetch.scm_url import ScmUrlFetch
from ansible_galaxy.fetch.local_file import LocalFileFetch
from ansible_galaxy.fetch.remote_url import RemoteUrlFetch
from ansible_galaxy.fetch.galaxy_url import GalaxyUrlFetch
from ansible_galaxy.models.content import CONTENT_TYPES
from ansible_galaxy.models.content import CONTENT_TYPE_DIR_MAP
from ansible_galaxy.models import content


log = logging.getLogger(__name__)

# has a GalaxyContentMeta FIXME: rename back to GalaxyContentData
# FIXME: erk, and a metadata (ie, ansible-galaxy.yml)
#
# can provide a ContentInstallInfo


# FIXME: do we have an enum like class for py2.6? worth a dep?
class FetchMethods(object):
    SCM_URL = 'SCM_URL'
    LOCAL_FILE = 'LOCAL_FILE'
    REMOTE_URL = 'REMOTE_URL'
    GALAXY_URL = 'GALAXY_URL'


def choose_content_fetch_method(scm_url=None, src=None):
    log.debug('scm_url=%s, src=%s', scm_url, src)
    if scm_url:
        # create tar file from scm url
        return FetchMethods.SCM_URL

    if not src:
        raise exceptions.GalaxyClientError("No valid content data found")

    if os.path.isfile(src):
        # installing a local tar.gz
        return FetchMethods.LOCAL_FILE

    if '://' in src:
        return FetchMethods.REMOTE_URL

    # if it doesnt look like anything else, assume it's galaxy
    return FetchMethods.GALAXY_URL


#        fetch_method = ScmUrlFetch(scm_url=scm_url, scm_spec=spec)
#        return fetch_method

# FIXME: really just three methods here, install, remove, fetch. install -> save, fetch -> load
#       remove -> delete
class GalaxyContent(object):

    SUPPORTED_SCMS = set(['git', 'hg'])
    META_INSTALL = os.path.join('meta', '.galaxy_install_info')
    ROLE_DIRS = ('defaults', 'files', 'handlers', 'meta', 'tasks', 'templates', 'vars', 'tests')
    NO_META = ('module', 'strategy_plugin')
    REQUIRES_META_MAIN = ('role')

    # FIXME(alikins): Not a fan of vars/args with names like 'type', but leave it for now
    def __init__(self, galaxy, name,
                 src=None, version=None, scm=None, path=None, type="role",
                 content_meta=None, sub_name=None,
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
        self.content_install_type = type
        content_type = type

        self._metadata = None

        self._install_info = None

        self.log = logging.getLogger(__name__ + '.' + self.__class__.__name__)

        self.display_callback = display_callback or display.display_callback

        # self.options = galaxy.options
        self.galaxy = galaxy

        # FIXME: validate_certs is an option for two different things,
        #        the connection to the galaxy_server (eg, galaxy.ansible.com)
        #        and to where archives are downloaded (eg, github)
        self._validate_certs = not galaxy.server['ignore_certs']

        # FIXME
        self.sub_name = sub_name

        # self.galaxy.content_roots['default']['content_path']
        primary_galaxy_content_path = self.galaxy.content_path

        # If the content requires a meta/main.yml file ala roles
        requires_meta_main = False
        if content_type in self.REQUIRES_META_MAIN:
            requires_meta_main = True

        self.content_meta = content_meta or \
            content.GalaxyContentMeta(name=name, src=src, version=version,
                                      scm=scm, path=primary_galaxy_content_path,
                                      requires_meta_main=requires_meta_main,
                                      content_type=content_type,
                                      content_dir=CONTENT_TYPE_DIR_MAP.get(content_type, None))

        if content_type not in CONTENT_TYPES and content_type != "all":
            raise exceptions.GalaxyClientError("%s is not a valid Galaxy Content Type" % content_type)

        # Set original path, needed to determine what action to take in order to
        # maintain backwards compat with legacy roles
        self._orig_path = path

    def __repr__(self):
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
        return self.content_meta.content_type

    @property
    def path(self):
        return self.content_meta.path

    @property
    def metadata(self):
        """
        Returns role metadata for type role, errors otherwise
        """
        if self.content_type in ["role", "all"]:
            if self._metadata is None:
                log.debug('content_meta.path: %s', self.content_meta.path)
                log.debug('archive.META_MAIN: %s', archive.META_MAIN)

                meta_path = os.path.join(self.content_meta.path, archive.META_MAIN)

                log.debug('meta_path: %s', meta_path)

                if os.path.isfile(meta_path):
                    try:
                        f = open(meta_path, 'r')
                        self._metadata = yaml.safe_load(f)
                    except Exception as e:
                        log.exception(e)
                        log.debug("Unable to load metadata for %s", self.content_meta.name)
                        return False
                    finally:
                        f.close()

            return self._metadata
        else:
            return {}

    # TODO: class/module for ContentInstallInfo
    @property
    def install_info(self):
        """
        Returns Galaxy Content install info
        """
        # FIXME: Do we want to have this for galaxy content?
        if self._install_info is None:
            log.debug('self.path: %s', self.path)
            log.debug('self.META_INSTALL: %s', self.META_INSTALL)

            info_path = os.path.join(self.path, self.META_INSTALL)

            log.debug('info_path: %s', info_path)
            if os.path.isfile(info_path):
                try:
                    f = open(info_path, 'r')
                    self._install_info = yaml.safe_load(f)
                except Exception as e:
                    log.exception(e)
                    self.debug("Unable to load Galaxy install info for %s", self.content_meta.name)
                    return False
                finally:
                    f.close()
        return self._install_info

    # FIXME: should probably be a GalaxyInfoInfo class
    def _write_galaxy_install_info(self):
        """
        Writes a YAML-formatted file to the role's meta/ directory
        (named .galaxy_install_info) which contains some information
        we can use later for commands like 'list' and 'info'.
        """
        # FIXME - unsure if we want this, need to figure it out and if we want it then need to handle
        #

        info = dict(
            version=self.version,
            install_date=datetime.datetime.utcnow().strftime("%c"),
        )
        if not os.path.exists(os.path.join(self.path, 'meta')):
            os.makedirs(os.path.join(self.path, 'meta'))
        info_path = os.path.join(self.path, self.META_INSTALL)
        with open(info_path, 'w+') as f:
            # FIXME: just return the install_info dict (or better, build it elsewhere and pass in)
            # FIXME: stop minging self state
            try:
                self._install_info = yaml.safe_dump(info, f)
            except Exception as e:
                log.warn('unable to serialize .galaxy_install_info to info_path=%s for data=%s', info_path, info)
                log.exception(e)
                return False

        return True

    def remove(self):
        """
        Removes the specified content from the content path.
        There is a sanity check to make sure there's a meta/main.yml or
        ansible-galaxy.yml file at this path so the user doesn't blow away
        random directories.
        """
        # FIXME - not yet implemented for non-role types
        if self.content_type == "role":
            if self.metadata:
                try:
                    rmtree(self.path)
                    return True
                except Exception as e:
                    log.warn('unable to rmtree for path=%s', self.path)
                    log.exception(e)
                    pass

        else:
            raise exceptions.GalaxyClientError("Removing Galaxy Content not yet implemented")

        return False

    def _build_download_url(self, src, external_url=None, version=None):
        if external_url and version:
            archive_url = '%s/archive/%s.tar.gz' % (external_url, version)
            return archive_url

        archive_url = src

        return archive_url

    def _install_for_content_types(self, content_tar_file, archive_parent_dir,
                                   content_archive_type=None, content_meta=None,
                                   content_types_to_install=None,
                                   content_sub_name=None,
                                   force_overwrite=False):

        all_installed_paths = []
        content_types_to_install = content_types_to_install or []
        for install_content_type in content_types_to_install:
            log.debug('INSTALLING %s type content from %s', install_content_type, content_tar_file)

            member_matches = archive.filter_members_by_content_type(content_tar_file,
                                                                    content_archive_type,
                                                                    content_type=install_content_type)

            # filter by path built from sub_dir and sub_name for 'modules/elasticsearch_plugin.py'
            content_sub_dir = content_meta.content_sub_dir or content.CONTENT_TYPE_DIR_MAP.get(install_content_type, '')

            # FIXME: probably should be using a more explicit content name->file name map if we have one, or
            #        at least figuring all this out before the install step.
            # if we are installing a single content from the repo, filter out everything else by path name matches
            if content_sub_name:
                match_pattern = '*/%s/%s*' % (content_sub_dir, content_sub_name)
                # log.debug('MATCH_PATTERNS: %s', match_pattern)

                member_matches = archive.filter_members_by_fnmatch(content_tar_file,
                                                                   match_pattern)
            log.debug('content_meta: %s', content_meta)
            log.info('about to extract %s to %s', content_meta.name, content_meta.path)

            installed_paths = archive.extract_by_content_type(content_tar_file,
                                                              archive_parent_dir,
                                                              content_meta,
                                                              content_archive_type=content_archive_type,
                                                              install_content_type=install_content_type,
                                                              files_to_extract=member_matches,
                                                              extract_to_path=content_meta.path,
                                                              force_overwrite=force_overwrite)
            all_installed_paths.extend(installed_paths)

        return all_installed_paths

    def _install_all(self, content_tar_file, archive_parent_dir,
                     content_archive_type=None, content_meta=None,
                     force_overwrite=False):

        # FIXME: not sure of best approach/pattern to figuring out how/where to extract the content too
        #        It is almost similar to a url rewrite engine. Or really, persisting of some object that was loaded from a DTO
        content_meta = content_meta or self.content_meta

        all_installed_paths = self._install_for_content_types(content_tar_file, archive_parent_dir,
                                                              content_archive_type, content_meta,
                                                              content_types_to_install=CONTENT_TYPES,
                                                              force_overwrite=force_overwrite)

        installed = [(content_meta, all_installed_paths)]
        return installed

    def _install_role_archive(self, content_tar_file, archive_parent_dir, content_meta,
                              force_overwrite=False):

        member_matches = archive.filter_members_by_content_meta(content_tar_file,
                                                                content_archive_type='role',
                                                                content_meta=content_meta)

        # log.debug('member_matches: %s' % member_matches)
        log.debug('content_meta: %s', content_meta)
        log.info('about to extract %s to %s', content_meta.name, content_meta.path)

        installed_paths = archive.extract_by_content_type(content_tar_file,
                                                          archive_parent_dir,
                                                          content_meta,
                                                          content_archive_type='role',
                                                          install_content_type='role',
                                                          files_to_extract=member_matches,
                                                          extract_to_path=content_meta.path,
                                                          force_overwrite=force_overwrite)

        installed = [(content_meta, installed_paths)]
        return installed

    def _install_apb_archive(self, content_tar_file, archive_parent_dir, content_meta,
                             force_overwrite=False):
        apb_name = content_meta.apb_data.get('name', content_meta.name)
        log.info('about to extract %s to %s', apb_name, content_meta.path)

        installed_paths = archive.extract_by_content_type(content_tar_file,
                                                          archive_parent_dir,
                                                          content_meta,
                                                          content_archive_type='apb',
                                                          install_content_type='apb',
                                                          files_to_extract=content_tar_file.getmembers(),
                                                          extract_to_path=content_meta.path,
                                                          force_overwrite=force_overwrite)

        installed = [(content_meta, installed_paths)]
        return installed

    def install(self, content_meta=None, force_overwrite=False):
        installed = []
        archive_role_metadata = None

        meta_file = None
        archive_parent_dir = None

        # FIXME: enum/constant/etc demagic
        content_archive_type = 'multi'

        content_meta = content_meta or self.content_meta

        # FIXME: really need to move the fetch step elsewhere and do it before,
        #        install should get pass a content_archive (or something more abstract)
        # TODO: some useful exceptions for 'cant find', 'cant read', 'cant write'
        fetch_method = choose_content_fetch_method(scm_url=self.scm, src=self.src)

        fetcher = None
        if fetch_method == FetchMethods.SCM_URL:
            fetcher = ScmUrlFetch(scm_url=self.scm, scm_spec=self.spec)
        elif fetch_method == FetchMethods.LOCAL_FILE:
            # the file is a tar, so open it that way and extract it
            # to the specified (or default) content directory
            fetcher = LocalFileFetch(self.src)
        elif fetch_method == FetchMethods.REMOTE_URL:
            fetcher = RemoteUrlFetch(remote_url=self.src, validate_certs=self._validate_certs)
        elif fetch_method == FetchMethods.GALAXY_URL:
            fetcher = GalaxyUrlFetch(content_spec=self.src,
                                     content_version=self.version,
                                     galaxy_context=self.galaxy,
                                     validate_certs=self._validate_certs)
        else:
            raise exceptions.GalaxyError('No approriate content fetcher found for %s %s',
                                         self.scm, self.src)

        log.debug('fetch_method: %s', fetch_method)

        if fetcher:
            content_archive = fetcher.fetch()

            log.debug('content_archive=%s', content_archive)

        if not content_archive:
            raise exceptions.GalaxyClientError('No valid content data found for %s', self.src)

        log.debug("installing from %s", content_archive)

        if not tarfile.is_tarfile(content_archive):
            raise exceptions.GalaxyClientError("the file downloaded was not a tar.gz")

        if content_archive.endswith('.gz'):
            content_tar_file = tarfile.open(content_archive, "r:gz")
        else:
            content_tar_file = tarfile.open(content_archive, "r")

        members = content_tar_file.getmembers()

        # next find the metadata file
        (meta_file, meta_parent_dir, galaxy_file, apb_yaml_file) = \
            archive.find_archive_metadata(members)

        # log.debug('self.content_type: %s', self.content_type)

        # content types like 'module' shouldn't care about meta_file elsewhere
        if self.content_type in self.NO_META:
            meta_file = None

        if not archive_parent_dir:
            archive_parent_dir = archive.find_archive_parent_dir(members, content_meta)

        log.debug('meta_file: %s', meta_file)
        log.debug('galaxy_file: %s', galaxy_file)
        log.debug('content_type: %s', content_meta.content_type)
        log.debug("archive_parent_dir: %s", archive_parent_dir)
        log.debug("meta_parent_dir: %s", meta_parent_dir)

        # if not meta_file and not galaxy_file and self.content_type == "role":
        #    raise exceptions.GalaxyClientError("this role does not appear to have a meta/main.yml file or ansible-galaxy.yml.")

        # Look for top level role metadata
        archive_role_metadata = \
            archive.load_archive_role_metadata(content_tar_file,
                                               os.path.join(archive_parent_dir, archive.META_MAIN))

        self._metadata = archive.load_archive_role_metadata(content_tar_file,
                                                            meta_file)

        galaxy_metadata = archive.load_archive_galaxyfile(content_tar_file,
                                                          galaxy_file)

        apb_data = archive.load_archive_apb_yaml(content_tar_file,
                                                 apb_yaml_file)

        log.debug('apb_data: %s', pprint.pformat(apb_data))

        # looks like we are a role, update the default content_type from all -> role
        if archive_role_metadata:
            log.debug('Find role metadata in the archive, so installing it as role content_type')
            log.debug('copying self.content_meta: %s', self.content_meta)

            data = self.content_meta.data

            content_meta = content.RoleContentArchiveMeta.from_data(data)

            log.debug('role content_meta: %s', content_meta)

            # we are dealing with an role archive
            content_archive_type = 'role'

        # TODO: truthiness of galaxy_metadata may be better, since that means it was parsed and non empty
        if galaxy_file:
            content_archive_type = 'galaxy'

        if apb_data:
            log.debug('Find APB metadata in the archive, so installing it as APB content_type')

            data = self.content_meta.data
            data['apb_data'] = apb_data

            content_meta = content.APBContentArchiveMeta.from_data(data)

            log.debug('APB content_meta: %s', content_meta)
            content_archive_type = 'apb'

        log.debug('content_archive_type=%s', content_archive_type)

        # we strip off any higher-level directories for all of the files contained within
        # the tar file here. The default is 'github_repo-target'. Gerrit instances, on the other
        # hand, does not have a parent directory at all.

        if not os.path.isdir(content_meta.path):
            log.debug('No content path (%s) found so creating it', content_meta.path)

            os.makedirs(content_meta.path)

        # TODO: need an install state machine real bad

        if self.content_type != "all":
            self.display_callback("- extracting %s %s to %s" % (self.content_type, content_meta.name, self.path))
        else:
            self.display_callback("- extracting all content in %s to content directories" % content_meta.name)

        log.info('Installing content of type: %s', content_meta.content_type)

        content_types_to_install = [self.content_install_type]
        if self.content_install_type == 'all':
            content_types_to_install = CONTENT_TYPES

        # now branch based on archive type
        if content_archive_type == 'galaxy':
            log.info('Installing %s as a content_archive_type=%s content_type=%s (galaxy_file)',
                     content_meta.name, content_archive_type, content_meta.content_type)
            log.debug('galaxy_file=%s', galaxy_file)
            log.debug('galaxy_metadata=%s', pprint.pformat(galaxy_metadata))

            # Parse the ansible-galaxy.yml file and install things
            # as necessary
            installed_from_galaxy_metadata =  \
                install_from_galaxy_metadata(content_tar_file,
                                             archive_parent_dir,
                                             galaxy_metadata,
                                             content_meta,
                                             display_callback=self.display_callback,
                                             force_overwrite=force_overwrite)

            installed.extend(installed_from_galaxy_metadata)

        elif content_archive_type == 'role':
            log.info('Installing %s as a role content archive and content_type=%s (role)', content_meta.name, content_meta.content_type)

            log.debug('archive_parent_dir: %s', archive_parent_dir)
            installed_from_role = self._install_role_archive(content_tar_file,
                                                             archive_parent_dir,
                                                             content_meta=content_meta,
                                                             force_overwrite=force_overwrite)
            installed.extend(installed_from_role)

        elif content_archive_type == 'apb':
            log.info('Installing %s as a Ansible Playbook Bundle content archive and content_type=%s (apb)', content_meta.name, content_meta.content_type)

            apb_name = content_meta.apb_data.get('name', content_meta.name)
            log.info('about to extract %s to %s', apb_name, content_meta.path)

            if self.content_install_type in ('all', 'apb'):
                installed_from_apb = \
                    self._install_apb_archive(content_tar_file,
                                              archive_parent_dir,
                                              content_meta=content_meta,
                                              force_overwrite=force_overwrite)

                installed.extend(installed_from_apb)

            else:
                # we are installing bits out of the apb, treat it like a multi-content
                content_meta.content_dir = None
                content_meta.content_sub_dir = None
                content_meta.content_type = 'all'

                installed_paths = \
                    self._install_for_content_types(content_tar_file,
                                                    archive_parent_dir,
                                                    content_archive_type='apb',
                                                    content_meta=content_meta,
                                                    # install_content_type='apb',
                                                    content_types_to_install=content_types_to_install,
                                                    force_overwrite=force_overwrite)

                installed_from_apb = [(content_meta, installed_paths)]

            installed.extend(installed_from_apb)
        # a multi content archive
        else:
            # if content_meta.content_type == 'all':

            log.info('Installing %s as a archive_type=%s content_type=%s install_type=%s ',
                     content_meta.name, content_archive_type, content_meta.content_type,
                     self.content_install_type)

            log.info('about to extract content_type=%s %s to %s',
                     content_meta.content_type, content_meta.name, content_meta.path)

            log.debug('content_meta: %s', content_meta)
            res = self._install_for_content_types(content_tar_file,
                                                  archive_parent_dir,
                                                  content_archive_type,
                                                  content_meta,
                                                  content_sub_name=self.sub_name,
                                                  content_types_to_install=content_types_to_install,
                                                  force_overwrite=force_overwrite)

            log.debug('res:\n%s', pprint.pformat(res))

            installed.append((content_meta, res))

        # return the parsed yaml metadata
        self.display_callback("- %s was installed successfully to %s" % (str(self), self.path))

        # rm any temp files created when getting the content archive
        fetcher.cleanup()

        # self.display_callback('Installed content: %s',

        for item in installed:
            log.info('Installed content: %s', item[0])
            log.debug('Installed files: %s', pprint.pformat(item[1]))
        return installed

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
