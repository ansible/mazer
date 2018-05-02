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
import errno
import fnmatch
import json
import logging
import os
import shutil
from shutil import rmtree
import six
import subprocess
import tarfile
import tempfile
import yaml

from distutils.version import LooseVersion

from ansible_galaxy.flat_rest_api.api import GalaxyAPI
from ansible_galaxy.config import defaults
from ansible_galaxy import exceptions
from ansible_galaxy.models.content import CONTENT_PLUGIN_TYPES, CONTENT_TYPES
from ansible_galaxy.models.content import CONTENT_TYPE_DIR_MAP, VALID_ROLE_SPEC_KEYS
from ansible_galaxy.models import content

from ansible_galaxy.flat_rest_api.urls import open_url

log = logging.getLogger(__name__)

# has a GalaxyContentMeta FIXME: rename back to GalaxyContentData
# FIXME: erk, and a metadata (ie, ansible-galaxy.yml)
#
# can provide a ContentInstallInfo


# TODO: test cases
# TODO: class/type for a content spec
def parse_content_name(content_name):
    "split a full content_name into username, content_name"

    repo_name = None
    try:
        parts = content_name.split(".")
        user_name = parts[0]
        if len(parts) > 2:
            repo_name = parts[1]
            content_name = '.'.join(parts[2:])
        else:
            content_name = '.'.join(parts[1:])
    except Exception as e:
        log.exception(e)
        raise exceptions.GalaxyClientError("Invalid content name (%s). Specify content as format: username.contentname" % content_name)

    return (user_name, repo_name, content_name)


def tar_info_content_name_match(tar_info, content_name, content_path=None):
    # only reg files or symlinks can match
    if not tar_info.isreg() and not tar_info.islnk():
        return False

    content_path = content_path or ""

    # TODO: test cases for patterns
    match_pattern = '*%s*' % content_name
    if content_path:
        match_pattern = '*/%s/%s*' % (content_path, content_name)

    # FIXME: would be better as two predicates both apply by comprehension
    if fnmatch.fnmatch(tar_info.name, match_pattern):
        return True

    return False


class GalaxyContent(object):

    SUPPORTED_SCMS = set(['git', 'hg'])
    META_MAIN = os.path.join('meta', 'main.yml')
    GALAXY_FILE = os.path.join('ansible-galaxy.yml')
    META_INSTALL = os.path.join('meta', '.galaxy_install_info')
    ROLE_DIRS = ('defaults', 'files', 'handlers', 'meta', 'tasks', 'templates', 'vars', 'tests')
    NO_META = ('module', 'plugin')

    # FIXME(alikins): Not a fan of vars/args with names like 'type', but leave it for now
    def __init__(self, galaxy, name,
                 src=None, version=None, scm=None, path=None, type="role",
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

        content_type = type

        self._metadata = None
        self._galaxy_metadata = None
        self._install_info = None
        self._validate_certs = not galaxy.options.ignore_certs

        self.log = logging.getLogger(__name__ + '.' + self.__class__.__name__)
        self.log.debug('Validate TLS certificates: %s', self._validate_certs)

        self.display_callback = display_callback or self._display_callback

        self.options = galaxy.options
        self.galaxy = galaxy

        self.content = content.GalaxyContentMeta(name=name, src=src, version=version,
                                                 scm=scm, path=path, content_type=content_type)
        # self.name = name
        # self.version = version
        # self.src = src or name
        # self.scm = scm

        # TODO: remove this when the data constructors are split
        # This is a marker needed to make certain decisions about single
        # content type vs all content found in the repository archive when
        # extracting files
        self._install_all_content = False
        if content_type == "all":
            self._install_all_content = True

        self._set_type(content_type)

        if self.content_type not in CONTENT_TYPES and self.content_type != "all":
            raise exceptions.GalaxyClientError("%s is not a valid Galaxy Content Type" % self.content_type)

        # Set original path, needed to determine what action to take in order to
        # maintain backwards compat with legacy roles
        self._orig_path = path

        # Set self.path and self.path_dir
        self._set_content_paths(path)

    def _display_callback(self, *args, **kwargs):
        level_arg = kwargs.pop('level', None)
        levels = {'warning': 'WARNING'}
        level = levels.get(level_arg, None)
        if level:
            print('%s' % level, *args)
        print(*args)

    def __repr__(self):
        """
        Returns "content_name (version) content_type" if version is not null
        Returns "content_name content_type" otherwise
        """
        if self.version:
            return "%s (%s) %s" % (self.content.name, self.version, self.content_type)
        else:
            return "%s %s" % (self.content.name, self.content_type)

    def __eq__(self, other):
        return self.content.name == other.content.name

    def _set_type(self, new_type):
        """
        Set the internal type information, because GalaxyContent can contain
        many different types this needs to be able to change state depending on
        content installation.

        This will update:
            self.content_type
            self.type_dir

        :param new_type: str, new content_type to assign
        """

        # FIXME - Anytime we change state like this, it feels wrong. Should
        #         probably evaluate a better way to do this.
        self.content_type = new_type

        # We need this because the type_dir inside a Galaxy Content archive is
        # not the same as it's installed location as per the CONTENT_TYPE_DIR_MAP
        # for some types
        self.type_dir = "%ss" % new_type

    def _set_content_paths(self, path=None):
        """
        Conditionally set content path based on content type
        """
        new_path_info = self._get_content_paths(path, content_type=self.content_type,
                                                content_name=self.content.name,
                                                galaxy_content_paths=self.galaxy.content_paths[:],
                                                install_all_content=self._install_all_content)
        self.log.debug('XXXXXXXXXXXXXXX new_path_info=%s', new_path_info)
        # FIXME: remove all the internal state tweaking
        # self.path is a property that returns self.content.path
        self.content.path = new_path_info['content_path']
        self.paths = new_path_info['content_paths']
        # FIXME: what is the diff between self.path and self.content.path ?
        self.content.path = new_path_info['content_content_path']
        self.galaxy.content_paths = new_path_info['galaxy_content_paths']
        self.content_type = new_path_info['content_type']
        self._install_all_content = new_path_info['install_all_content']

    def _get_content_paths(self, path=None, content_name=None, content_type=None,
                           galaxy_content_paths=None,
                           content_content_path=None,
                           install_all_content=None):
        """
        Return a tuple of content path info

        returns (content_path, content_paths, galaxy_content_path,
                 content_type, install_all_content, content_content_path)
        """
        content_paths = ""  # FIXME - handle multiple content types here
        content_path = None
        content_content_path = content_content_path
        new_content_type = content_type
        # FIXME: cp for now, will need to pass in value
        galaxy_content_paths = galaxy_content_paths or []
        install_all_content = install_all_content or False

        # FIXME - ":" is a placeholder default value for --content_path in the
        #         galaxy cli and it should really not be
        if path is not None and path != ":":
            # "all" doesn't actually exist, but it's an internal idea that means
            # "we're going to install everything", however that comes with the
            # caveot of needing to inspect to find out if there's a meta/main.yml
            # and handling a legacy role type accordingly
            if content_name not in path and new_content_type in ["role", "all"]:
                path = os.path.join(path, content_name)
            # self.path = path
            content_path = path

            # We need for first set self.path (as we did above) in order to then
            # allow the property function "metadata" to check for the existence
            # of a meta/main.yml and it not, then we don't join the name to the
            # end of the path because it's not necessary for non-role content
            # types as they aren't namespaced by directory
            if not self.metadata:
                content_path = path
            else:
                # If we find a meta/main.yml, this is a legacy role and we need
                # to handle it
                new_content_type = 'role'
                # self._set_type("role")
                # self._install_all_content = False
                install_all_content = False

            content_paths = [content_path]
        else:
            # First, populate the self.galaxy.content_paths for processing below

            # Unfortunately this exception is needed and we can't easily rely
            # on the dir_map because there's not consistency of plural vs
            # singular of type between the contants vars read in from the config
            # file and the subdirectories
            if new_content_type != "all":
                self.log.debug('ctdm: %s', json.dumps(CONTENT_TYPE_DIR_MAP, indent=4))
                galaxy_content_paths = [os.path.join(os.path.expanduser(p),
                                                     CONTENT_TYPE_DIR_MAP[new_content_type]) for p in defaults.DEFAULT_CONTENT_PATH]
            else:
                galaxy_content_paths = defaults.DEFAULT_CONTENT_PATH

            # use the first path by default
            if new_content_type == "role":
                content_content_path = os.path.join(galaxy_content_paths[0], content_name)
            else:
                content_content_path = galaxy_content_paths[0]
            # create list of possible paths
            content_paths = [x for x in galaxy_content_paths]
            content_paths = [os.path.join(x, content_name) for x in content_paths]

        return {'content_path': content_path,
                'content_paths': content_paths,
                'galaxy_content_paths': galaxy_content_paths,
                'content_type': new_content_type,
                'install_all_content': install_all_content,
                'content_content_path': content_content_path}

    # FIXME: update calling code instead?
    @property
    def name(self):
        return self.content.name

    @property
    def version(self):
        return self.content.version

    @property
    def src(self):
        return self.content.src

    @property
    def scm(self):
        return self.content.scm

    @property
    def content_dir(self):
        return self.content.content_dir

    @property
    def path(self):
        return self.content.path

    @property
    def metadata(self):
        """
        Returns role metadata for type role, errors otherwise
        """
        if self.content_type in ["role", "all"]:
            if self._metadata is None:
                meta_path = os.path.join(self.content.path, self.META_MAIN)
                if os.path.isfile(meta_path):
                    try:
                        f = open(meta_path, 'r')
                        self._metadata = yaml.safe_load(f)
                    except Exception as e:
                        self.log.exception(e)
                        self.log.debug("Unable to load metadata for %s", self.content.name)
                        return False
                    finally:
                        f.close()

            return self._metadata
        else:
            return {}

    @property
    def galaxy_metadata(self):
        """
        Returns Galaxy Content metadata, found in ansible-galaxy.info
        """
        if self._galaxy_metadata is None:
            gmeta_path = os.path.join(self.path, self.GALAXY_FILE)
            if os.path.isfile(gmeta_path):
                try:
                    with open(gmeta_path, 'r') as f:
                        self._galaxy_metadata = yaml.safe_load(f)
                except Exception as e:
                    self.log.exception(e)
                    self.log.debug("Unable to load galaxy metadata for %s", self.content.name)
                    return False

        return self._galaxy_metadata

    # TODO: class/module for ContentInstallInfo
    @property
    def install_info(self):
        """
        Returns Galaxy Content install info
        """
        # FIXME: Do we want to have this for galaxy content?
        if self._install_info is None:

            info_path = os.path.join(self.path, self.META_INSTALL)
            if os.path.isfile(info_path):
                try:
                    f = open(info_path, 'r')
                    self._install_info = yaml.safe_load(f)
                except Exception as e:
                    self.log.exception(e)
                    self.debug("Unable to load Galaxy install info for %s", self.content.name)
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
                self.log.warn('unable to serialize .galaxy_install_info to info_path=%s for data=%s', info_path, info)
                self.log.exception(e)
                return False

        return True

    # FIXME: persisting of content archives or subsets thereof
    # FIXME: currently does way too much, could be split into generic and special case classes
    # FIXME: some weirdness here is caused by tarfile API being a little strange. To extract a file
    #        to a different path than from the archive, you have to update each TarInfo member and
    #        change it's 'name' attribute after loading/opening a TarFile() but before extract()
    #        Since it's mutating the TarFile object, have to be careful if anything will use the object
    #        after it was changed
    def _write_archived_files(self, tar_file, parent_dir,
                              file_name=None, files_to_extract=None,
                              extract_to_path=None):
        """
        Extract and write out files from the archive, this is a common operation
        needed for both old-roles and new-style galaxy content, the main
        difference is parent directory

        :param tar_file: tarfile, the local archive of the galaxy content files
        :param parent_dir: str, parent directory path to extract to
        :kwarg file_name: str, specific filename to extract from parent_dir in archive
        """
        # now we do the actual extraction to the path
        self.log.debug('tar_file=%s, parent_dir=%s, file_name=%s', tar_file, parent_dir, file_name)
        files_to_extract = files_to_extract or []
        plugin_found = None

        if file_name:
            files_to_extract.append(file_name)
        self.log.debug('files_to_extract: %s', files_to_extract)

        path = extract_to_path or self.path

        # do we need to drive this from tar_file members if we have file_names_to_extract?
        # for member in tar_file.getmembers():
        for member in files_to_extract:
            # Have to preserve this to reset it for the sake of processing the
            # same TarFile object many times when handling an ansible-galaxy.yml
            # file
            orig_name = member.name
            # self.log.debug('member.name=%s', member.name)
            self.log.debug('member=%s, orig_name=%s, member.isreg()=%s member.issym()=%s',
                           member, orig_name, member.isreg(), member.issym())
            # we only extract files, and remove any relative path
            # bits that might be in the file for security purposes
            # and drop any containing directory, as mentioned above
            # TODO: could we use tar_info_content_name_match with a '*' patter here to
            #       get a files_to_extract?
            if member.isreg() or member.issym():
                parts_list = member.name.split(os.sep)

                self.log.debug('content_type: %s', self.content_type)
                # filter subdirs if provided
                if self.content_type != "role":
                    # Check if the member name (path), minus the tar
                    # archive baseir starts with a subdir we're checking
                    # for
                    self.log.debug('parts_list: %s', parts_list)
                    self.log.debug('parts_list[1]: %s', parts_list[1])
                    self.log.debug('CONTENT_TYPE_DIR_MAP[self.content_type]: %s', CONTENT_TYPE_DIR_MAP[self.content_type])
                    if file_name:
                        # The parent_dir passed in when a file name is specified
                        # should be the full path to the file_name as defined in the
                        # ansible-galaxy.yml file. If that matches the member.name
                        # then we've found our match.
                        if member.name == os.path.join(parent_dir, file_name):
                            # lstrip self.content.name because that's going to be the
                            # archive directory name and we don't need/want that
                            plugin_found = parent_dir.lstrip(self.content.name)

                    elif len(parts_list) > 1 and parts_list[1] == CONTENT_TYPE_DIR_MAP[self.content_type]:
                        plugin_found = CONTENT_TYPE_DIR_MAP[self.content_type]

                    self.log.debug('plugin_found1: %s', plugin_found)
                    if not plugin_found:
                        continue

                self.log.debug('plugin_found2: %s', plugin_found)
                if plugin_found:
                    # If this is not a role, we don't expect it to be installed
                    # into a subdir under roles path but instead directly
                    # where it needs to be so that it can immediately be used
                    #
                    # FIXME - are galaxy content types namespaced? if so,
                    #         how do we want to express their path and/or
                    #         filename upon install?
                    if plugin_found == 'library':
                        # subdir_index = parts_list.index(plugin_found)
                        parts = [parts_list[-1]]
                    else:
                        if plugin_found in parts_list:
                            subdir_index = parts_list.index(plugin_found) + 1
                            parts = parts_list[subdir_index:]
                        else:
                            # The desired subdir has been identified but the
                            # current member belongs to another subdir so just
                            # skip it
                            continue
                else:
                    parts = member.name.replace(parent_dir, "", 1).split(os.sep)
                    self.log.debug('plugin_found falsey, building parts: %s', parts)

                final_parts = []
                for part in parts:
                    if part != '..' and '~' not in part and '$' not in part:
                        final_parts.append(part)
                member.name = os.path.join(*final_parts)
                self.log.debug('final_parts: %s', final_parts)

                if self.content_type in CONTENT_PLUGIN_TYPES:
                    self.display_callback(
                        "-- extracting %s %s from %s into %s" %
                        (self.content_type, member.name, self.content.name, os.path.join(path, member.name))
                    )
                if os.path.exists(os.path.join(path, member.name)) and not getattr(self.options, "force", False):
                    if self.content_type in CONTENT_PLUGIN_TYPES:
                        message = (
                            "the specified Galaxy Content %s appears to already exist." % os.path.join(path, member.name),
                            "Use of --force for non-role Galaxy Content Type is not yet supported"
                        )
                        if self._install_all_content:
                            # FIXME - Probably a better way to handle this
                            self.display_callback(" ".join(message), level='warning')
                        else:
                            raise exceptions.GalaxyClientError(" ".join(message))
                    else:
                        message = "the specified role %s appears to already exist. Use --force to replace it." % self.content.name
                        if self._install_all_content:
                            # FIXME - Probably a better way to handle this
                            self.display_callback(message, level='warning')
                        else:
                            raise exceptions.GalaxyClientError(message)

                # Alright, *now* actually write the file
                self.log.debug('Extracting member=%s, path=%s', member, path)
                tar_file.extract(member, path)

                # Reset the name so we're on equal playing field for the sake of
                # re-processing this TarFile object as we iterate through entries
                # in an ansible-galaxy.yml file
                member.name = orig_name

        if self.content_type != "role" and self.content_type not in self.NO_META:
            if not plugin_found:
                raise exceptions.GalaxyClientError("Required subdirectory not found in Galaxy Content archive for %s" % self.content.name)

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
                    self.log.warn('unable to rmtree for path=%s', self.path)
                    self.log.exception(e)
                    pass

        else:
            raise exceptions.GalaxyClientError("Removing Galaxy Content not yet implemented")

        return False

    # FIXME: let the archive_url be passed in
    def fetch(self, content_data, external_url=None):
        """
        Downloads the archived content from github to a temp location
        """

        # self.log.debug('fetch content_data=%s', json.dumps(content_data, indent=4))
        # FIXME: return early if content_data is falsey and unindent
        if content_data:

            archive_url = self.src

            # FIXME: 'github_user'/'github_repo' dont exist in v3 API
            # first grab the file and save it to a temp location
            if "github_user" in content_data and "github_repo" in content_data:
                archive_url = 'https://github.com/%s/%s/archive/%s.tar.gz' % (content_data["github_user"], content_data["github_repo"], self.version)

            if external_url:
                archive_url = '%s/archive/%s.tar.gz' % (external_url, self.version)

            self.log.debug('self.src=%s archive_url=%s', self.src, archive_url)

            self.display_callback("- downloading content from %s" % archive_url)

            try:
                url_file = open_url(archive_url, validate_certs=self._validate_certs)
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                data = url_file.read()
                while data:
                    temp_file.write(data)
                    data = url_file.read()
                temp_file.close()
                return temp_file.name
            except Exception as e:
                # FIXME: there is a ton of reasons a download and save could fail so could likely provided better errors here
                self.log.exception(e)
                self.display_callback("failed to download the file: %s" % str(e), level='error')

        return False

    # TODO: split this up, it's pretty gnarly
    def install(self):
        # the file is a tar, so open it that way and extract it
        # to the specified (or default) content directory
        local_file = False

        # ContentArchive
        #   path: None
        #   scm_info: ScmInfo()
        #   galaxy_content:
        #     username
        #     namespace
        #     repo_name
        #     content_name
        #     versions: []
        #     repository:
        #       external_url:
        #     scm_branch: ?
        #     archive_url:
        #   contents:
        #    - name: content1
        #      meta_file:
        #        role_name:
        #        version:
        #        deps:
        #      galaxy_metadata:
        #        whichever_data:
        #        other_ansible_galaxy_yml_data:
        #      path_in_archive:
        #      path_to_install_to:
        #      content_type:
        #    - name: content2
        #      <..>
        #
        # FIXME: this is loading and persisting the archive and should be extract to another class/method
        # FIXME: the exception case is no self.scm and no self.src, so detect that early and raise then unindent
        if self.scm:
            # create tar file from scm url
            tmp_file = GalaxyContent.scm_archive_content(**self.spec)
        elif self.src:
            if os.path.isfile(self.src):
                # installing a local tar.gz
                local_file = True
                tmp_file = self.src
            elif '://' in self.src:
                content_data = self.src
                tmp_file = self.fetch(content_data)
            else:
                # FIXME: all this stuff that hits galaxy api to eventually find the archive url should be extract elsewhere
                api = GalaxyAPI(self.galaxy)
                # FIXME - Need to update our API calls once Galaxy has them implemented
                content_username, repo_name, content_name = parse_content_name(self.src)
                self.log.debug('content_username=%s, repo_name=%s content_name=%s', content_username, repo_name, content_name)
                # TODO: extract parsing of cli content sorta-url thing and add better tests
                repo_name = repo_name or content_name
                content_data = api.lookup_content_repo_by_name(content_username, repo_name)
                if not content_data:
                    raise exceptions.GalaxyClientError("- sorry, %s was not found on %s." % (self.src, api.api_server))

                if content_data.get('role_type') == 'APP':
                    # Container Role
                    self.display_callback("%s is a Container App role, and should only be installed using Ansible "
                                          "Container" % self.content.name, level='warning')

                # FIXME - Need to update our API calls once Galaxy has them implemented
                related = content_data.get('related', {})
                related_versions_url = related.get('versions', None)
                content_versions = api.fetch_content_related(related_versions_url)

                # FIXME: mv to it's own method
                if not self.version:
                    # convert the version names to LooseVersion objects
                    # and sort them to get the latest version. If there
                    # are no versions in the list, we'll grab the head
                    # of the master branch
                    if len(content_versions) > 0:
                        loose_versions = [LooseVersion(a.get('name', None)) for a in content_versions]
                        try:
                            loose_versions.sort()
                        except TypeError:
                            raise exceptions.GalaxyClientError(
                                'Unable to compare content versions (%s) to determine the most recent version due to incompatible version formats. '
                                'Please contact the content author to resolve versioning conflicts, or specify an explicit content version to '
                                'install.' % ', '.join([v.vstring for v in loose_versions])
                            )
                        self.content.version = str(loose_versions[-1])
                    # FIXME: follow 'repository' branch and it's ['import_branch'] ?
                    elif content_data.get('github_branch', None):
                        self.content.version = content_data['github_branch']
                    else:
                        self.content.version = 'master'
                elif self.version != 'master':
                    if content_versions and str(self.version) not in [a.get('name', None) for a in content_versions]:
                        raise exceptions.GalaxyError(
                            "- the specified version (%s) of %s was not found in the list of available versions (%s)." % (self.version,
                                                                                                                          self.content.name,
                                                                                                                          content_versions))
                related_repo_url = related.get('repository', None)
                content_repo = None
                if related_repo_url:
                    content_repo = api.fetch_content_related(related_repo_url)
                self.log.debug('content_repo: %s', content_repo)

                external_url = content_repo.get('external_url', None)
                if external_url:
                    tmp_file = self.fetch(content_data, external_url)
                else:
                    tmp_file = self.fetch(content_data)

        else:
            raise exceptions.GalaxyClientError("No valid content data found")

        # FIXME: the 'fetch', persist locally,  and 'install' steps should not be combined here
        # FIXME: mv to own method[s], unindent
        if tmp_file:

            self.log.debug("installing from %s", tmp_file)

            # FIXME: unindent the non error else here
            if not tarfile.is_tarfile(tmp_file):
                raise exceptions.GalaxyClientError("the file downloaded was not a tar.gz")
            else:
                if tmp_file.endswith('.gz'):
                    content_tar_file = tarfile.open(tmp_file, "r:gz")
                else:
                    content_tar_file = tarfile.open(tmp_file, "r")
                # verify the role's meta file

                meta_file = None
                galaxy_file = None
                archive_parent_dir = None
                members = content_tar_file.getmembers()
                # import pprint
                # self.log.debug('tmp_file (%s) members: %s', tmp_file, pprint.pformat(members))
                # next find the metadata file

                # FIXME: mv to method or ditch entirely and drive from a iterable of files to extract and save
                # FIXME: this is role specific logic so could move elsewhere
                for member in members:
                    if self.META_MAIN in member.name or self.GALAXY_FILE in member.name:
                        # Look for parent of meta/main.yml
                        # Due to possibility of sub roles each containing meta/main.yml
                        # look for shortest length parent
                        meta_parent_dir = os.path.dirname(os.path.dirname(member.name))
                        if not meta_file:
                            archive_parent_dir = meta_parent_dir
                            if self.GALAXY_FILE in member.name:
                                galaxy_file = member
                            else:
                                meta_file = member
                        else:
                            #self.log.debug('meta_parent_dir: %s archive_parent_dir: %s len(m): %s len(a): %s member.name: %s',
                            #               meta_parent_dir, archive_parent_dir,
                            #               len(meta_parent_dir),
                            #               len(archive_parent_dir),
                            #               member.name)
                            if len(meta_parent_dir) < len(archive_parent_dir):
                                archive_parent_dir = meta_parent_dir
                                meta_file = member
                                if self.GALAXY_FILE in member.name:
                                    galaxy_file = member
                                else:
                                    meta_file = member

                self.log.debug('self.content_type: %s', self.content_type)

                # content types like 'module' shouldn't care about meta_file elsewhere
                if self.content_type in self.NO_META:
                    meta_file = None

                # FIXME: THIS IS A HACK
                #
                # We've determined that this is a legacy role, we're going to
                # change state and re-eval paths for backwards compat with the
                # legacy role type
                if self.content_type == "all" and meta_file:
                    self._set_type("role")
                    self._set_content_paths(self._orig_path)
                    self._install_all_content = False

                # FIXME: mv to it's own method
                if not archive_parent_dir:
                    # archive_parent_dir wasn't found above when checking for metadata files
                    parent_dir_found = False
                    for member in members:
                        # This is either a new-type Galaxy Content that doesn't have an
                        # ansible-galaxy.yml file and the type desired is specified and
                        # we check parent dir based on the correct subdir existing or
                        # we need to just scan the subdirs heuristically and figure out
                        # what to do
                        if self.content_type != "all":
                            if self.type_dir in member.name:
                                archive_parent_dir = os.path.dirname(member.name)
                                parent_dir_found = True
                                break
                        else:
                            for plugin_dir in CONTENT_TYPE_DIR_MAP.values():
                                if plugin_dir in member.name:
                                    archive_parent_dir = os.path.dirname(member.name)
                                    parent_dir_found = True
                                    break
                            if parent_dir_found:
                                break

                    if not parent_dir_found:
                        if self.content_type in CONTENT_PLUGIN_TYPES:
                            msg = "No content metadata provided, nor content directories found for content_type: %s" % self.content_type
                            raise exceptions.GalaxyClientError(msg)

                self.log.debug("meta_file: %s galaxy_file: %s self.content_type: %s", meta_file, galaxy_file, self.content_type)
                self.log.debug("archive_parent_dir: %s", archive_parent_dir)
                self.log.debug("meta_parent_dir: %s", meta_parent_dir)
                if not meta_file and not galaxy_file and self.content_type == "role":
                    raise exceptions.GalaxyClientError("this role does not appear to have a meta/main.yml file or ansible-galaxy.yml.")
                # FIXME: unindent
                else:
                    # FIXME: mv to AnsibleGalaxyMetadata
                    try:
                        if galaxy_file:
                            # Let the galaxy_file take precedence
                            self._galaxy_metadata = yaml.safe_load(content_tar_file.extractfile(galaxy_file))
                        elif meta_file:
                            self._metadata = yaml.safe_load(content_tar_file.extractfile(meta_file))
                        # else:
                        # FIXME - Need to handle the scenario where we "walk the dirs" and place things where they should be
                    except Exception as e:
                        self.warn('unable to extract and yaml load galaxy_file=%s meta_file=%s tmpfile=%s', galaxy_file, meta_file, tmp_file)
                        self.log.exception(e)
                        raise exceptions.GalaxyClientError("this role does not appear to have a valid meta/main.yml or ansible-galaxy.yml file.")

                # we strip off any higher-level directories for all of the files contained within
                # the tar file here. The default is 'github_repo-target'. Gerrit instances, on the other
                # hand, does not have a parent directory at all.

                installed = False
                # FIXME: get rid of the while loop or continue if nothing catches
                while not installed:
                    if self.content_type != "all":
                        self.display_callback("- extracting %s %s to %s" % (self.content_type, self.content.name, self.path))
                    else:
                        self.display_callback("- extracting all content in %s to content directories" % self.content.name)

                    # FIXME: a few pages of code in a try block, extract to own method/class
                    try:
                        # FIXME: figure out what the 'case' is first, then branch to implementations and mv the impls
                        if self.content_type == "role" and meta_file and not galaxy_file:
                            # This is an old-style role
                            # FIXME: should likely be responsibilty of the Content or RoleContent serializer
                            if os.path.exists(self.path):
                                if not os.path.isdir(self.path):
                                    raise exceptions.GalaxyClientError("the specified roles path exists and is not a directory.")
                                elif not getattr(self.options, "force", False):
                                    msg = "the specified role %s appears to already exist. Use --force to replace it." % self.content.name
                                    raise exceptions.GalaxyClientError(msg)
                                else:
                                    # using --force, remove the old path
                                    # FIXME: this is ~10 indent levels deep in the 'install' method which is a weird place to do a remove
                                    if not self.remove():
                                        raise exceptions.GalaxyClientError("%s doesn't appear to contain a role.\n  please remove this directory manually if you really "
                                                        "want to put the role here." % self.path)
                            else:
                                os.makedirs(self.path)

                            # FIXME: not sure of best approach/pattern to figuring out how/where to extract the content too
                            #        It is almost similar to a url rewrite engine. Or really, persisting of some object that was loaded from a DTO
                            tar_file_members = content_tar_file.getmembers()
                            member_matches = [tar_file_member for tar_file_member in tar_file_members if tar_info_content_name_match(tar_file_member, content_name)]
                            self.log.debug('member_matches: %s' % member_matches)
                            self._write_archived_files(content_tar_file, archive_parent_dir, files_to_extract=member_matches,
                                                        extract_to_path=self.content.path)

                            # self._write_archived_files(content_tar_file, archive_parent_dir)

                            # write out the install info file for later use
                            self._write_galaxy_install_info()
                            installed = True
                        elif galaxy_file:
                            # Parse the ansible-galaxy.yml file and install things
                            # as necessary

                            # FIXME - need to handle the scenario where we want
                            #         all content types defined in the ansible-galaxy.yml file

                            for content in self.galaxy_metadata:
                                # The galaxy_metadata will contain a dict that defines
                                # a section for each content type to be installed
                                # and then a list of types with their deps and src
                                #
                                # FIXME - Link to permanent public spec once it exists
                                #
                                # https://github.com/ansible/galaxy/issues/245
                                # https://etherpad.net/p/Galaxy_Metadata
                                #
                                # Example to install modules with module_utils deps:
                                ########
                                #meta_version: '0.1'  #metadata format version
                                #modules:
                                # - path: playbooks/modules/*
                                # - path: modules/module_b
                                #   dependencies:
                                #     - src: /module_utils
                                # - path: modules/module_c.py
                                #   dependencies:
                                #     - src: namespace.repo_name.module_name
                                #       type: module_utils
                                #     - src: ssh://git@github.com/acme/ansible-example.git
                                #       type: module_utils
                                #       version: master
                                #       scm: git
                                #       path: common/utils/*
                                #- src: namespace.repo_name.plugin_name
                                #       type: action_plugin
                                #######
                                #
                                #
                                # Handle "modules" for MVP, add more types later
                                #
                                # A more generic way would be to do this, but we're
                                # not "there yet"
                                #   if content == self.type_dir:
                                #
                                #   self.galaxy_metadata[content] # General processing

                                # FIXME: suppose this is basically options for setting up a deserializer
                                # FIXME: def should be elsewhere, likely some serializer class
                                if content == "meta_version":
                                    continue
                                elif content == "modules":
                                    self._set_type("module")
                                    self._set_content_paths()
                                    for module in self.galaxy_metadata[content]:
                                        if len(module["path"].split(os.sep)) > 1:
                                            if module["path"].split(os.sep)[-1] in ['/', '*']:
                                                # Handle the glob or designation of entire directory install
                                                self._write_archived_files(content_tar_file, os.path.join(archive_parent_dir, module['path']))
                                                installed = True
                                            else:
                                                self._write_archived_files(
                                                    content_tar_file,
                                                    os.path.join(archive_parent_dir, os.path.dirname(module['path'])),
                                                    file_name=module['path'].split(os.sep)[-1]
                                                )
                                                installed = True

                                        # FIXME: on a general level, having content that only sometimes has dep info seems like a problem
                                        if 'dependencies' in module:
                                            for dep in module['dependencies']:
                                                if 'src' not in dep:
                                                    raise exceptions.GalaxyClientError("ansible-galaxy.yml dependencies must provide a src")

                                                dep_content_info = GalaxyContent.yaml_parse(dep['src'])
                                                # FIXME - Should we assume this to be true for module deps?
                                                dep_content_info["type"] = "module_util"

                                                self.display_callback('- processing dependency: %s' % dep_content_info["src"])

                                                # This is an external dep, treat it as such
                                                if dep_content_info["scm"]:
                                                    dep_content = GalaxyContent(self.galaxy, **dep_content_info)
                                                    try:
                                                        installed = dep_content.install()
                                                    except exceptions.GalaxyClientError as e:
                                                        self.display_callback("- dependency %s was NOT installed successfully: %s " %
                                                                              (dep_content.name, str(e)), level='warning')
                                                        continue
                                                else:
                                                    # Local dep, just install it
                                                    self._set_type("module_util")
                                                    self._set_content_paths()
                                                    if len(dep["src"].split(os.sep)) > 1:
                                                        if dep["src"].split(os.sep)[-1] in ['/', '*']:
                                                            # Handle the glob or designation of entire directory install
                                                            self._write_archived_files(content_tar_file, os.path.join(archive_parent_dir, dep['src']))
                                                            installed = True
                                                        else:
                                                            self._write_archived_files(
                                                                content_tar_file,
                                                                os.path.join(archive_parent_dir, os.path.dirname(dep['src'])),
                                                                file_name=dep['src'].split(os.sep)[-1]
                                                            )
                                                            installed = True

                                else:
                                    # FIXME - add more types other than module here
                                    raise exceptions.GalaxyClientError("ansible-galaxy.yml install not yet supported for content_type %s" % self.content_type)

                        elif not meta_file and not galaxy_file:
                            # No meta/main.yml found so it's not a legacy role
                            # and no galaxyfile found, so assume it's a new
                            # galaxy content type and attempt to install it by
                            # heuristically walking the directories and install
                            # the appropriate things in the appropriate places

                            # FIXME: this is basically a big switch to decide what serializer to use
                            if self.content_type != "all":
                                # TODO: based on content_name, need to find/build the full path to that in the
                                #       tar archive so we can extract it.
                                #       ie, alikins.testing-content.elastic_search.py
                                #       full path would be:
                                #         ansible-testing-content-master/library/database/misc/elasticsearch_plugin.py
                                #       Then we pass that into _write_archive_files as file_name arg

                                # tar info for each file, so we can filter on filename match and file type
                                tar_file_members = content_tar_file.getmembers()
                                member_matches = [tar_file_member for tar_file_member in tar_file_members if tar_info_content_name_match(tar_file_member, content_name)]
                                self.log.debug('member_matches: %s' % member_matches)
                                self._write_archived_files(content_tar_file, archive_parent_dir, files_to_extract=member_matches,
                                                           extract_to_path=self.content.path)
                                installed = True
                            else:
                                # FIXME: extract and test, build a map of the name transforms first, then apply, then install
                                # Find out what plugin type subdirs exist in this repo
                                #
                                # This list comprehension will iterate every member entry in
                                # the tarfile, split it's name by os.sep and drop the top most
                                # parent dir, which will be self.content.name (we don't want it as it's
                                # not needed for plugin types. First make sure the length of
                                # that split and drop of parent dir is length > 1 and verify
                                # that the subdir is infact in CONTENT_TYPE_DIR_MAP.values()
                                #
                                # This should give us a list of valid content type subdirs
                                # found heuristically within this Galaxy Content repo
                                #
                                plugin_subdirs = [
                                    os.path.join(m.name.split(os.sep)[1:])[0]
                                        for m in members
                                            if len(os.path.join(m.name.split(os.sep)[1:])) > 1
                                            and os.path.join(m.name.split(os.sep)[1:])[0] in CONTENT_TYPE_DIR_MAP.values()
                                ]

                                if plugin_subdirs:
                                    # FIXME: stop munging state
                                    self._install_all_content = True
                                    for plugin_subdir in plugin_subdirs:
                                        # Set the type, this is neccesary for processing extraction of
                                        # the tarball content
                                        #
                                        # rstrip the letter 's' from the plugin type subdir, this should
                                        # be the type
                                        self._set_type(plugin_subdir.rstrip('s'))
                                        self._set_content_paths(None)
                                        self._write_archived_files(content_tar_file, archive_parent_dir)
                                        installed = True
                                else:
                                    raise exceptions.GalaxyClientError("This Galaxy Content does not contain valid content subdirectories, expected any of: %s "
                                                                       % CONTENT_TYPES)
                        else:
                            raise exceptions.GalaxyClientError('Cant figure out what install method to use')

                    except OSError as e:
                        error = True
                        # FIXME: what is this doing? walking down dir tree ?
                        if e.errno == errno.EACCES and len(self.paths) > 1:
                            current = self.paths.index(self.path)
                            if len(self.paths) > current:
                                self.path = self.paths[current + 1]
                                error = False
                        if error:
                            raise exceptions.GalaxyClientError("Could not update files in %s: %s" % (self.path, str(e)))

                # return the parsed yaml metadata
                self.display_callback("- %s was installed successfully" % str(self))
                if not local_file:
                    try:
                        self.log.info("Not removing the tmp_file %s", tmp_file)
                        # os.unlink(tmp_file)
                    except (OSError, IOError) as e:
                        self.warn('Unable to remove tmp file (%s): %s' % (tmp_file, str(e)))
                        self.display_callback("Unable to remove tmp file (%s): %s" % (tmp_file, str(e)), level='warning')
                return True

        return False

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
        return dict(scm=self.scm, src=self.src, version=self.version, name=self.content.name)

    # FIXME: dont see any reason not to mv this somewhere more general
    @staticmethod
    def scm_archive_content(src, scm='git', name=None, version='HEAD'):
        """
        Archive a Galaxy Content SCM repo locally

        Implementation originally adopted from the Ansible RoleRequirement
        """
        if scm not in ['hg', 'git']:
            raise exceptions.GalaxyClientError("- scm %s is not currently supported" % scm)
        tempdir = tempfile.mkdtemp()
        clone_cmd = [scm, 'clone', src, name]
        with open('/dev/null', 'w') as devnull:
            try:
                popen = subprocess.Popen(clone_cmd, cwd=tempdir, stdout=devnull, stderr=devnull)
            except Exception as e:
                raise exceptions.GalaxyClientError("error executing: %s" % " ".join(clone_cmd))
            rc = popen.wait()
        if rc != 0:
            raise exceptions.GalaxyClientError("- command %s failed in directory %s (rc=%s)" % (' '.join(clone_cmd), tempdir, rc))

        if scm == 'git' and version:
            checkout_cmd = [scm, 'checkout', version]
            with open('/dev/null', 'w') as devnull:
                try:
                    popen = subprocess.Popen(checkout_cmd, cwd=os.path.join(tempdir, name), stdout=devnull, stderr=devnull)
                except (IOError, OSError):
                    raise exceptions.GalaxyClientError("error executing: %s" % " ".join(checkout_cmd))
                rc = popen.wait()
            if rc != 0:
                raise exceptions.GalaxyClientError("- command %s failed in directory %s (rc=%s)" % (' '.join(checkout_cmd), tempdir, rc))

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.tar')
        if scm == 'hg':
            archive_cmd = ['hg', 'archive', '--prefix', "%s/" % name]
            if version:
                archive_cmd.extend(['-r', version])
            archive_cmd.append(temp_file.name)
        if scm == 'git':
            archive_cmd = ['git', 'archive', '--prefix=%s/' % name, '--output=%s' % temp_file.name]
            if version:
                archive_cmd.append(version)
            else:
                archive_cmd.append('HEAD')

        with open('/dev/null', 'w') as devnull:
            popen = subprocess.Popen(archive_cmd, cwd=os.path.join(tempdir, name),
                                     stderr=devnull, stdout=devnull)
            rc = popen.wait()
        if rc != 0:
            raise exceptions.GalaxyClientError("- command %s failed in directory %s (rc=%s)" % (' '.join(archive_cmd), tempdir, rc))

        shutil.rmtree(tempdir, ignore_errors=True)
        return temp_file.name

    # TODO: return a new GalaxyContentMeta
    # TODO: dont munge the passed in content
    # TODO: split into smaller methods
    # FIXME: does this actually use yaml?
    # FIXME: kind of seems like this does two different things
    @staticmethod
    def yaml_parse(content):
        """parses the passed in yaml string and returns a dict with name/src/scm/version

        Or... if the passed in 'content' is a dict, it either creates role or if not a role,
        it copies the dict and sets name/src/scm/version in it"""

        # TODO: move to own method
        if isinstance(content, six.string_types):
            name = None
            scm = None
            src = None
            version = None
            if ',' in content:
                if content.count(',') == 1:
                    (src, version) = content.strip().split(',', 1)
                elif content.count(',') == 2:
                    (src, version, name) = content.strip().split(',', 2)
                else:
                    raise exceptions.GalaxyClientError("Invalid content line (%s). Proper format is 'content_name[,version[,name]]'" % content)
            else:
                src = content

            if name is None:
                name = GalaxyContent.repo_url_to_content_name(src)
            if '+' in src:
                (scm, src) = src.split('+', 1)

            return dict(name=name, src=src, scm=scm, version=version)

        # Not sure what will/should happen if content is not a Mapping or a string
        if 'role' in content:
            name = content['role']
            if ',' in name:
                # Old style: {role: "galaxy.role,version,name", other_vars: "here" }
                # Maintained for backwards compat
                content = GalaxyContent.role_spec_parse(content['role'])
            else:
                del content['role']
                content['name'] = name
        else:
            content = content.copy()

            if 'src'in content:
                # New style: { src: 'galaxy.role,version,name', other_vars: "here" }
                if 'github.com' in content["src"] and 'http' in content["src"] and '+' not in content["src"] and not content["src"].endswith('.tar.gz'):
                    content["src"] = "git+" + content["src"]

                if '+' in content["src"]:
                    (scm, src) = content["src"].split('+')
                    content["scm"] = scm
                    content["src"] = src

                if 'name' not in content:
                    content["name"] = GalaxyContent.repo_url_to_content_name(content["src"])

            if 'version' not in content:
                content['version'] = ''

            if 'scm' not in content:
                content['scm'] = None

        for key in list(content.keys()):
            if key not in VALID_ROLE_SPEC_KEYS:
                content.pop(key)

        return content

    @staticmethod
    def repo_url_to_content_name(repo_url):
        # gets the role name out of a repo like
        # http://git.example.com/repos/repo.git" => "repo"

        if '://' not in repo_url and '@' not in repo_url:
            return repo_url
        trailing_path = repo_url.split('/')[-1]
        if trailing_path.endswith('.git'):
            trailing_path = trailing_path[:-4]
        if trailing_path.endswith('.tar.gz'):
            trailing_path = trailing_path[:-7]
        if ',' in trailing_path:
            trailing_path = trailing_path.split(',')[0]
        return trailing_path

    # FIXME: likely needs to learn version=1,name='blip', etc. And tests
    @staticmethod
    def role_spec_parse(role_spec):
        # takes a repo and a version like
        # git+http://git.example.com/repos/repo.git,v1.0
        # and returns a list of properties such as:
        # {
        #   'scm': 'git',
        #   'src': 'http://git.example.com/repos/repo.git',
        #   'version': 'v1.0',
        #   'name': 'repo'
        # }
        log.warning("The comma separated role spec format, use the yaml/explicit format instead. Line that trigger this: %s (version='2.7')", role_spec)

        default_role_versions = dict(git='master', hg='tip')

        role_spec = role_spec.strip()
        role_version = ''
        if role_spec == "" or role_spec.startswith("#"):
            return (None, None, None, None)

        tokens = [s.strip() for s in role_spec.split(',')]

        # assume https://github.com URLs are git+https:// URLs and not
        # tarballs unless they end in '.zip'
        if 'github.com/' in tokens[0] and not tokens[0].startswith("git+") and not tokens[0].endswith('.tar.gz'):
            tokens[0] = 'git+' + tokens[0]

        if '+' in tokens[0]:
            (scm, role_url) = tokens[0].split('+')
        else:
            scm = None
            role_url = tokens[0]

        if len(tokens) >= 2:
            role_version = tokens[1]

        if len(tokens) == 3:
            role_name = tokens[2]
        else:
            role_name = GalaxyContent.repo_url_to_content_name(tokens[0])

        if scm and not role_version:
            role_version = default_role_versions.get(scm, '')

        return dict(scm=scm, src=role_url, version=role_version, name=role_name)
