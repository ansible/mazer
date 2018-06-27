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
import yaml

from ansible_galaxy import exceptions
from ansible_galaxy import archive
from ansible_galaxy import content_archive
from ansible_galaxy.content_repo_galaxy_metadata import install_from_galaxy_metadata
from ansible_galaxy import display
from ansible_galaxy.fetch.scm_url import ScmUrlFetch
from ansible_galaxy.fetch.local_file import LocalFileFetch
from ansible_galaxy.fetch.remote_url import RemoteUrlFetch
from ansible_galaxy.fetch.galaxy_url import GalaxyUrlFetch
from ansible_galaxy.models.content import CONTENT_TYPES, SUPPORTED_CONTENT_TYPES
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
# TODO: add InstalledContent
#       get rid of GalaxyContent.metadata / GalaxyContent.install_info
#       for InstalledContent add a from_install_info() to build it from file at creation
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
    def __init__(self, galaxy, name,
                 src=None, version=None, scm=None, path=None, type="role",
                 content_meta=None, sub_name=None, namespace=None,
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
        self.content_install_type = type
        content_type = type

        self._metadata = metadata

        self._install_info = install_info

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
        # requires_meta_main = False
        # if content_type in self.REQUIRES_META_MAIN:
        #    requires_meta_main = True

        self.content_meta = content_meta or \
            content.GalaxyContentMeta(name=name, src=src, version=version,
                                      scm=scm, path=primary_galaxy_content_path,
                                      namespace=namespace,
                                      # requires_meta_main=requires_meta_main,
                                      content_type=content_type,
                                      content_dir=CONTENT_TYPE_DIR_MAP.get(content_type, None))

        # TODO: factory? metaclass?
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
        return self.content_meta.content_type

    @property
    def path(self):
        return self.content_meta.path

    @property
    def metadata(self):
        return self._metadata

    @property
    def install_info(self):
        return self._install_info

    # TODO: this is pretty much the persist/save method
    # FIXME: should probably be a GalaxyInfoInfo class
    def _write_galaxy_install_info(self, content_meta, info_path):
        """
        Writes a YAML-formatted file to the role's meta/ directory
        (named .galaxy_install_info) which contains some information
        we can use later for commands like 'list' and 'info'.
        """
        # FIXME - unsure if we want this, need to figure it out and if we want it then need to handle
        #

        install_date = datetime.datetime.utcnow()
        info = dict(
            version=content_meta.version,
            # This format is locale specific, but preserve for compat
            install_date=install_date.strftime("%c"),
            install_date_iso=install_date
        )

        # if not os.path.exists(os.path.join(content_meta.path, 'meta')):
        if not os.path.exists(os.path.dirname(info_path)):
            os.makedirs(os.path.dirname(info_path))

        with open(info_path, 'w+') as f:
            # FIXME: just return the install_info dict (or better, build it elsewhere and pass in)
            # FIXME: stop minging self state
            try:
                self._install_info = yaml.safe_dump(info, f, default_flow_style=False)
            except Exception as e:
                log.warn('unable to serialize .galaxy_install_info to info_path=%s for data=%s', info_path, info)
                log.exception(e)
                return False

        log.debug('wrote %s galaxy_install_info to %s', content_meta.name, info_path)
        return True

    def remove(self):
        raise exceptions.GalaxyError('Calling remove() on a GalaxyContent (not InstalledGalaxyContent) doesnt mean anything')

    def _install_for_content_types(self, content_tar_file, archive_parent_dir,
                                   content_archive_type=None, content_meta=None,
                                   content_types_to_install=None,
                                   content_sub_name=None,
                                   force_overwrite=False):

        all_installed_paths = []
        content_types_to_install = content_types_to_install or []

        tar_file_members = content_tar_file.getmembers()

        for install_content_type in content_types_to_install:
            log.debug('INSTALLING %s type content from %s', install_content_type, content_tar_file)

            # TODO: install_for_content_type()  - handle one content type
            #       _install_for_content_type_role() - role specific impl
            # TODO:  install_contents()  - iterator over all the contents of a content type (ie, 'roles')
            # TODO:   install_content()  - install a single content  (ie, a role)
            #         _install_content_role()  - role specific impl of install_content
            content_type_member_matches = archive.filter_members_by_content_type(tar_file_members,
                                                                                 content_archive_type,
                                                                                 content_type=install_content_type)

            # filter by path built from sub_dir and sub_name for 'modules/elasticsearch_plugin.py'
            content_sub_dir = content_meta.content_sub_dir or content.CONTENT_TYPE_DIR_MAP.get(install_content_type, '')

            log.debug('content_meta: %s', content_meta)
            log.info('about to extract %s to %s', content_meta.name, content_meta.path)
            log.info('content_sub_dir: %s', content_sub_dir)

            # log.debug('content_type_member_matches: %s', pprint.pformat(content_type_member_matches))

            # TODO: extract_file_list_to_path(content_tar_file, files_to_extract, extract_to_path, force_overwrite)
            # TODO: split into lists of each content objects (ie, each role, instead of all roles) and
            #       install them one by one

            parent_dir = content_tar_file.members[0].name
            content_names = set()

            for content_type_member_match in content_type_member_matches:
                path_parts = content_type_member_match.name.split('/')
                # 0 is archive parent dir, 1 is content type (roles, modules, etc)
                # 2 is the content_name (role name, pluginfoo.py etc)
                content_names.add(path_parts[2])

            # content_names is all of the diffierent contents of install_content_type
            log.debug('content_names: %s', content_names)

            # namespace_repo_name = content_meta.src
            namespace_repo_name = '%s.%s' % (content_meta.namespace, content_meta.name)
            log.debug('namespace_repo_name: %s', namespace_repo_name)

            # extract each content individually
            for content_name in content_names:
                files_to_extract = []

                match_pattern = '%s/%s/%s*' % (parent_dir, content_sub_dir, content_name)

                member_matches = archive.filter_members_by_fnmatch(tar_file_members,
                                                                   match_pattern)

                namespaced_content_path = '%s/%s/%s' % (namespace_repo_name,
                                                        content_sub_dir,
                                                        content_name)

                log.debug('namespaced_content_path: %s', namespaced_content_path)

                for member_match in member_matches:
                    # archive_member, dest_dir, dest_filename, force_overwrite

                    # rel_path ~  roles/some-role/meta/main.yml for ex
                    rel_path = member_match.name[len(parent_dir) + 1:]

                    # need to replace the role name in the archive with the role name
                    # that includes the galaxy namespace

                    namespaced_role_rel_path = rel_path.replace('%s/%s' % (content_sub_dir,
                                                                           content_name),
                                                                namespaced_content_path,
                                                                1)

                    extract_info = {'archive_member': member_match,
                                    'dest_dir': content_meta.path,
                                    'dest_filename': namespaced_role_rel_path,
                                    'force_overwrite': force_overwrite}

                    files_to_extract.append(extract_info)

                # log.debug('files_to_extract: %s', pprint.pformat(files_to_extract))

                file_extractor = archive.extract_files(content_tar_file, files_to_extract)

                installed_paths = [x for x in file_extractor]
                all_installed_paths.extend(installed_paths)

                if install_content_type in self.REQUIRES_META_MAIN:
                    info_path = os.path.join(content_meta.path,
                                             namespaced_content_path,
                                             self.META_INSTALL)
                    self._write_galaxy_install_info(content_meta, info_path)

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

    # FIXME: This should really be shared with the bulk of install_for_content_type()
    #        and like a content type specific impl in a GalaxyContent subclass
    def _install_role_archive(self, content_tar_file, archive_meta, content_meta,
                              force_overwrite=False):

        log.debug('content_meta: %s', content_meta)

        if not content_meta.namespace:
            raise exceptions.GalaxyError('While installing a role from %s, no namespace was found. Try providing one with --namespace' %
                                         content_meta.src)

        log.debug('content_meta: %s', content_meta)
        log.info('about to extract %s to %s', content_meta.name, content_meta.path)

        tar_members = content_tar_file.members
        parent_dir = tar_members[0].name

        # repo_name = content_meta.name
        # namespace = content_meta.namespace
        namespace_repo_name = "%s.%s" % (content_meta.namespace, content_meta.name)

        log.debug('namespace_repo_name: %s', namespace_repo_name)

        namespaced_content_path = '%s/%s/%s' % (namespace_repo_name,
                                                'roles',
                                                content_meta.name)

        log.debug('namespace: %s', content_meta.namespace)
        log.debug('namespaced_content_path: %s', namespaced_content_path)

        files_to_extract = []
        for member in tar_members:
            # rel_path ~  roles/some-role/meta/main.yml for ex
            rel_path = member.name[len(parent_dir) + 1:]

            namespaced_role_rel_path = os.path.join(namespace_repo_name, 'roles', content_meta.name, rel_path)

            # log.debug('namespaced_role_rel_path: %s', namespaced_role_rel_path)

            extract_info = {'archive_member': member,
                            'dest_dir': content_meta.path,
                            'dest_filename': namespaced_role_rel_path,
                            'force_overwrite': force_overwrite}

            files_to_extract.append(extract_info)

        file_extractor = archive.extract_files(content_tar_file, files_to_extract)
        log.debug('file_extracter: %s', file_extractor)

        installed_paths = [x for x in file_extractor]
        installed = [(content_meta, installed_paths)]

        info_path = os.path.join(content_meta.path,
                                 namespaced_content_path,
                                 self.META_INSTALL)

        self._write_galaxy_install_info(content_meta, info_path)

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

    def install(self, content_meta=None, force_overwrite=False, namespace=None):
        installed = []
        archive_parent_dir = None

        # FIXME: enum/constant/etc demagic
        # content_archive_type = 'multi'

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
            try:
                fetch_results = fetcher.fetch()
            except exceptions.GalaxyDownloadError as e:
                log.exception(e)

                blurb = 'Failed to fetch the content archive "%s": %s'
                log.error(blurb, fetcher.remote_resource, e)

                # reraise, currently handled in main
                # TODO: if we support more than one archive per invocation, will need to accumulate errors
                #       if we want to skip some of them
                raise

            archive_path = fetch_results['archive_path']

        if not archive_path:
            raise exceptions.GalaxyClientError('No valid content data found for %s', self.src)

        log.debug("installing from %s", archive_path)

        content_tar_file, archive_meta = content_archive.load_archive(archive_path)

        content_data = fetch_results.get('content', {})
        content_meta.version = content_data.get('fetched_version', content_meta.version)
        content_meta.namespace = content_data.get('content_namespace', content_meta.namespace)

        log.debug('archive_meta: %s', archive_meta)

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

        log.info('Installing content from archive type: %s', archive_meta.archive_type)

        # content_types_to_install = [self.content_install_type]
        # if self.content_install_type == 'all':
        #    content_types_to_install = CONTENT_TYPES

        if archive_meta.archive_type == 'multi-content':
            # if content_meta.content_type == 'all':

            log.info('Installing %s as a archive_type=%s content_type=%s install_type=%s ',
                     content_meta.name, archive_meta.archive_type, content_meta.content_type,
                     self.content_install_type)

            log.info('about to extract content_type=%s %s version=%s to %s',
                     content_meta.content_type, content_meta.name, content_meta.version, content_meta.path)

            log.debug('content_meta: %s', content_meta)

            content_types_to_install = [self.content_install_type]
            if self.content_install_type == 'all':
                content_types_to_install = SUPPORTED_CONTENT_TYPES

            # content_type_parent_dir =
            res = self._install_for_content_types(content_tar_file,
                                                  archive_parent_dir,
                                                  archive_meta.archive_type,
                                                  content_meta,
                                                  content_sub_name=self.sub_name,
                                                  content_types_to_install=content_types_to_install,
                                                  force_overwrite=force_overwrite)

            # log.debug('res:\n%s', pprint.pformat(res))

            installed.append((content_meta, res))

        # now branch based on archive type
        # FIXME/TODO: not really used at the moment
        elif archive_meta.archive_type == 'galaxy':
            log.info('Installing %s as a archive_type=%s content_type=%s (galaxy_file)',
                     content_meta.name, archive_meta, content_meta.content_type)
            # log.debug('galaxy_file=%s', galaxy_file)
            # log.debug('galaxy_metadata=%s', pprint.pformat(galaxy_metadata))

            galaxy_metadata = None
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

        elif archive_meta.archive_type == 'role':
            log.info('Installing %s as a role content archive and content_type=%s (role)', content_meta.name, content_meta.content_type)

            log.debug('archive_parent_dir: %s', archive_parent_dir)
            installed_from_role = self._install_role_archive(content_tar_file,
                                                             archive_meta=archive_meta,
                                                             content_meta=content_meta,
                                                             force_overwrite=force_overwrite)
            installed.extend(installed_from_role)

        elif archive_meta.archive_type == 'apb':
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


# TODO/FIXME: revist a Content base class
class InstalledContent(GalaxyContent):
    def _load_metadata_yaml(self):
        meta_path = os.path.join(self.path,
                                 content_archive.META_MAIN)

        log.debug('looking for content meta data from meta_path: %s', meta_path)

        if os.path.isfile(meta_path):
            log.debug('loading content metadata from meta_path: %s', meta_path)
            try:
                f = open(meta_path, 'r')
                return yaml.safe_load(f)
            except Exception as e:
                log.exception(e)
                log.debug("Unable to load metadata for %s", self.content_meta.name)
                return False
            finally:
                f.close()

    @property
    def metadata(self):
        """
        Returns role metadata for type role, errors otherwise
        """
        if self.content_meta.content_type not in ('role', 'all'):
            log.debug('content_type not role %s', self.content_meta.content_type)
            return {}

        if self._metadata is not None:
            self._metadata = self._load_metadata_yaml()

        return self._metadata

    def _load_install_info(self):
        '''loads, yaml parses, and returns the data from .galaxy_install_info'''

#        log.debug('self.path: %s', self.path)
#        log.debug('self.META_INSTALL: %s', self.META_INSTALL)

        info_path = os.path.join(self.path, self.META_INSTALL)

        log.debug('info_path: %s', info_path)
        if os.path.isfile(info_path):
            try:
                f = open(info_path, 'r')
                return yaml.safe_load(f)
            except Exception as e:
                log.exception(e)
                self.debug("Unable to load Galaxy install info for %s", self.content_meta.name)
                return False
            finally:
                f.close()

    # TODO: class/module for ContentInstallInfo
    @property
    def install_info(self):
        """
        Returns Galaxy Content install info
        """
        # FIXME: Do we want to have this for galaxy content?
        if self._install_info is None:
            self._install_info = self._load_install_info()
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
