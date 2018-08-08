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
# import pprint
from shutil import rmtree

import attr

from ansible_galaxy import exceptions
from ansible_galaxy import archive
from ansible_galaxy import content_archive
from ansible_galaxy import install_info
from ansible_galaxy import role_metadata
from ansible_galaxy import display
from ansible_galaxy.fetch import fetch_factory
from ansible_galaxy.models.content import CONTENT_TYPES, SUPPORTED_CONTENT_TYPES
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
    def __init__(self,
                 galaxy,
                 name,
                 src=None,
                 version=None,
                 scm=None,
                 path=None,
                 type="role",
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
                                      content_type=content_type,
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
            log.debug('Installing %s type content from %s', install_content_type, content_tar_file)

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

            label = "%s.%s" % (content_meta.namespace, content_meta.name)
            log.debug('content_meta: %s', content_meta)

            log.info('About to extract "%s" to %s', label, content_meta.path)
            # log.info('content_sub_dir: %s', content_sub_dir)

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
            # namespace_repo_name = '%s.%s' % (content_meta.namespace, content_meta.name)
            # log.debug('namespace_repo_name: %s', namespace_repo_name)

            # extract each content individually
            for content_name in content_names:
                files_to_extract = []

                # TODO: This only works for roles/apbs that have a dir matching the content
                #       name. For other content like plugins or modules, we need to match
                #       on parent_dir/content_sub_dir/content_name (/modules/my_module.py)
                match_pattern = '%s/%s/%s/*' % (parent_dir, content_sub_dir, content_name)

                member_matches = archive.filter_members_by_fnmatch(tar_file_members,
                                                                   match_pattern)

                namespaced_content_path = '%s/%s/%s/%s' % (content_meta.namespace,
                                                           content_meta.name,
                                                           content_sub_dir,
                                                           content_name)

                log.debug('Extracting "%s" to %s', label, namespaced_content_path)

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

                    install_datetime = datetime.datetime.utcnow()

                    content_install_info = InstallInfo.from_version_date(version=content_meta.version,
                                                                         install_datetime=install_datetime)

                    install_info.save(content_install_info, info_path)
                    # self._write_galaxy_install_info(content_meta, info_path)

        return all_installed_paths

    # FIXME: This should really be shared with the bulk of install_for_content_type()
    #        and like a content type specific impl in a GalaxyContent subclass
    def _install_role_archive(self, content_tar_file, archive_meta, content_meta,
                              force_overwrite=False):

        if not content_meta.namespace:
            raise exceptions.GalaxyError('While installing a role from %s, no namespace was found. Try providing one with --namespace' %
                                         content_meta.src)

        label = "%s.%s" % (content_meta.namespace, content_meta.name)
        log.debug('content_meta: %s', content_meta)

        log.info('About to extract "%s" to %s', label, content_meta.path)

        tar_members = content_tar_file.members
        parent_dir = tar_members[0].name

        # repo_name = content_meta.name
        # namespace = content_meta.namespace

        namespaced_content_path = '%s/%s/%s/%s' % (content_meta.namespace,
                                                   content_meta.name,
                                                   'roles',
                                                   content_meta.name)

        # log.debug('namespace: %s', content_meta.namespace)
        log.debug('namespaced role path: %s', namespaced_content_path)

        files_to_extract = []
        for member in tar_members:
            # rel_path ~  roles/some-role/meta/main.yml for ex
            rel_path = member.name[len(parent_dir) + 1:]

            # namespaced_role_rel_path = os.path.join(namespace_repo_name, 'roles', content_meta.name, rel_path)
            namespaced_role_rel_path = os.path.join(content_meta.namespace, content_meta.name,  'roles', content_meta.name, rel_path)

            # log.debug('namespaced_role_rel_path: %s', namespaced_role_rel_path)

            extract_info = {'archive_member': member,
                            'dest_dir': content_meta.path,
                            'dest_filename': namespaced_role_rel_path,
                            'force_overwrite': force_overwrite}

            files_to_extract.append(extract_info)

        file_extractor = archive.extract_files(content_tar_file, files_to_extract)

        installed_paths = [x for x in file_extractor]
        installed = [(content_meta, installed_paths)]

        info_path = os.path.join(content_meta.path,
                                 namespaced_content_path,
                                 self.META_INSTALL)

        install_datetime = datetime.datetime.utcnow()

        content_install_info = InstallInfo.from_version_date(version=content_meta.version,
                                                             install_datetime=install_datetime)

        install_info.save(content_install_info, info_path)

        return installed

    def find(self):
        """find/discover info about the content

        This is all side effect, setting self._find_results."""

        log.debug('Attempting to find() content_spec=%s', self.content_spec)

        self._fetcher = fetch_factory.get(galaxy_context=self.galaxy,
                                          content_spec=self.content_spec)

        # TODO: sep method, called from actions.install
        self._find_results = self._fetcher.find()

        log.debug('find() found info for %s', self.content_spec)

    def fetch(self):
        """download the archive and side effect set self._archive_path to where it was downloaded to.

        MUST be called after self.find()."""

        log.debug('Fetching %s', self.content_spec)

        try:
            # FIXME: note that ignore_certs for the galaxy
            # server(galaxy_context.server['ignore_certs'])
            # does not really imply that the repo archive download should ignore certs as well
            # (galaxy api server vs cdn) but for now, we use the value for both
            fetch_results = self._fetcher.fetch(find_results=self._find_results)
        except exceptions.GalaxyDownloadError as e:
            log.exception(e)

            blurb = 'Failed to fetch the content archive "%s": %s'
            log.error(blurb, self._fetcher.remote_resource, e)

            # reraise, currently handled in main
            # TODO: if we support more than one archive per invocation, will need to accumulate errors
            #       if we want to skip some of them
            raise

        self._fetch_results = fetch_results
        self._archive_path = fetch_results['archive_path']

        return fetch_results

    def install(self, content_meta=None, force_overwrite=False):
        """extract the archive to the filesystem and write out install metadata.

        MUST be called after self.fetch()."""

        log.debug('install: content_meta=%s, force_overwrite=%s',
                  content_meta, force_overwrite)
        installed = []
        archive_parent_dir = None

        # FIXME: enum/constant/etc demagic
        # content_archive_type = 'multi'

        content_meta = content_meta or self.content_meta

        # FIXME: really need to move the fetch step elsewhere and do it before,
        #        install should get pass a content_archive (or something more abstract)
        # TODO: some useful exceptions for 'cant find', 'cant read', 'cant write'

        archive_path = self._fetch_results.get('archive_path', None)

        if not archive_path:
            raise exceptions.GalaxyClientError('No valid content data found for %s', self.src)

        log.debug("installing from %s", archive_path)

        content_tar_file, archive_meta = content_archive.load_archive(archive_path)

        # TODO: do we still need to check the fetched version against the spec version?
        content_data = self._fetch_results.get('content', {})

        # If the requested namespace/version is different than the one we got via find()/fetch()...
        if content_data.get('fetched_version', content_meta.version) != content_meta.version:
            log.info('Version "%s" for %s was requested but fetch found version "%s"',
                     content_meta.version, '%s.%s' % (content_meta.namespace, content_meta.name),
                     content_data.get('fetched_version', content_meta.version))

            content_meta = attr.evolve(content_meta, version=content_data['fetched_version'])

        if content_data.get('content_namespace', content_meta.namespace) != content_meta.namespace:
            log.info('Namespace "%s" for %s was requested but fetch found namespace "%s"',
                     content_meta.namespace, '%s.%s' % (content_meta.namespace, content_meta.name),
                     content_data.get('content_namespace', content_meta.namespace))

            content_meta = attr.evolve(content_meta, namespace=content_data['content_namespace'])

        log.debug('archive_meta: %s', archive_meta)

        # we strip off any higher-level directories for all of the files contained within
        # the tar file here. The default is 'github_repo-target'. Gerrit instances, on the other
        # hand, does not have a parent directory at all.

        if not os.path.isdir(content_meta.path):
            log.debug('No content path (%s) found so creating it', content_meta.path)

            os.makedirs(content_meta.path)

        # TODO: need an install state machine real bad

        if self.content_type != "all":
            self.display_callback('- extracting %s "%s" to %s' % (self.content_type, content_meta.name, self.path))
        else:
            self.display_callback("- extracting all content in %s to content directories" % content_meta.name)

        log.info('Installing content from archive type: %s', archive_meta.archive_type)

        if archive_meta.archive_type == 'multi-content':
            log.info('Installing "%s" as a archive_type=%s content_type=%s install_type=%s ',
                     content_meta.name, archive_meta.archive_type, content_meta.content_type,
                     self.content_install_type)

            log.info('About to extract content_type=%s "%s" version=%s to %s',
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

            installed.append((content_meta, res))

        elif archive_meta.archive_type == 'role':
            log.info('Installing "%s" as a role content archive and content_type=%s (role)', content_meta.name, content_meta.content_type)

            # log.debug('archive_parent_dir: %s', archive_parent_dir)

            installed_from_role = self._install_role_archive(content_tar_file,
                                                             archive_meta=archive_meta,
                                                             content_meta=content_meta,
                                                             force_overwrite=force_overwrite)
            installed.extend(installed_from_role)

        install_datetime = datetime.datetime.utcnow()

        repo_info_path = os.path.join(content_meta.path,
                                      self.content_meta.namespace,
                                      self.content_meta.name,
                                      '.galaxy_install_info')

        repo_install_info = InstallInfo.from_version_date(version=content_meta.version,
                                                          install_datetime=install_datetime)

        log.debug('repo_info_path: %s', repo_info_path)
        install_info.save(repo_install_info, repo_info_path)

        # return the parsed yaml metadata
        self.display_callback("- %s was installed successfully to %s" % (str(self), self.path))

        # rm any temp files created when getting the content archive
        self._fetcher.cleanup()

        for item in installed:
            log.info('Installed content: %s', item[0])
            # log.debug('Installed files: %s', pprint.pformat(item[1]))

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
    @property
    def metadata_path(self):
        return os.path.join(self.path, self.content_meta.namespace, self.content_meta.name,
                            self.content_meta.content_dir, self.content_meta.name, content_archive.META_MAIN)

    @property
    def metadata(self):
        """
        Returns role metadata for type role, errors otherwise
        """
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
