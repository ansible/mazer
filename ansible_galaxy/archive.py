# attempt to abstract (tar) archive handling a bit

# would like a easy way to extract a subdir of a tar archive to
# a directory on local fs while using relative paths

import fnmatch
import logging
import os
import yaml


import pprint



from ansible_galaxy import exceptions
from ansible_galaxy.models.content import CONTENT_TYPE_DIR_MAP, CONTENT_PLUGIN_TYPES
from ansible_galaxy.models import content_repository

log = logging.getLogger(__name__)

# pass in list of tarinfo of paths to extract
# pass in a map of tar member paths -> dest paths, built separately?
#  (based on content_type and CONTENT_TYPE_DIR_MAP etc)


def default_display_callback(*args, **kwargs):
    # log.debug('args=%s, kwargs=%s', args, kwargs)

    print(''.join(args))

# for plugins and everything except roles
# extract_content_by_content_type(content_type, base_path=None)

# for roles
# extract_content_by_role_name(role_name)

# def content_type_match(content_type, member_path):


# TODO:

# TODO: better place to define?
META_MAIN = os.path.join('meta', 'main.yml')
GALAXY_FILE = 'ansible-galaxy.yml'


# TODO/FIXME: try to make sense of this and find_archive_parent_dir
def find_archive_metadata(archive_members):
    '''Try to find the paths to the archives meta data files

    Aka, meta/main.yml or ansible-galaxy.yml.

    Also, while we are at it, try to find the archive parent
    dir.'''

    meta_file = None
    galaxy_file = None

    meta_parent_dir = None
    archive_parent_dir = None

    for member in archive_members:
        if META_MAIN in member.name or GALAXY_FILE in member.name:
            # Look for parent of meta/main.yml
            # Due to possibility of sub roles each containing meta/main.yml
            # look for shortest length parent
            meta_parent_dir = os.path.dirname(os.path.dirname(member.name))
            if not meta_file:
                archive_parent_dir = meta_parent_dir
                if GALAXY_FILE in member.name:
                    galaxy_file = member
                else:
                    meta_file = member
            else:
                # self.log.debug('meta_parent_dir: %s archive_parent_dir: %s len(m): %s len(a): %s member.name: %s',
                #               meta_parent_dir, archive_parent_dir,
                #               len(meta_parent_dir),
                #               len(archive_parent_dir),
                #               member.name)
                if len(meta_parent_dir) < len(archive_parent_dir):
                    archive_parent_dir = meta_parent_dir
                    meta_file = member
                    if GALAXY_FILE in member.name:
                        galaxy_file = member
                    else:
                        meta_file = member

    # FIXME: return a real type/object for archive metadata
    return (meta_file,
            meta_parent_dir,
            galaxy_file,
            archive_parent_dir)


def find_archive_parent_dir(archive_members, content_meta):
    # archive_parent_dir wasn't found when checking for metadata files
    archive_parent_dir = None

    for member in archive_members:
        # This is either a new-type Galaxy Content that doesn't have an
        # ansible-galaxy.yml file and the type desired is specified and
        # we check parent dir based on the correct subdir existing or
        # we need to just scan the subdirs heuristically and figure out
        # what to do
        if content_meta.content_type != "all":
            if content_meta.content_dir in member.name:
                archive_parent_dir = os.path.dirname(member.name)
                return archive_parent_dir
        else:
            for plugin_dir in CONTENT_TYPE_DIR_MAP.values():
                if plugin_dir in member.name:
                    archive_parent_dir = os.path.dirname(member.name)
                    return archive_parent_dir

    if content_meta.content_type not in CONTENT_PLUGIN_TYPES:
        return archive_parent_dir

    # TODO: archive format exception?
    msg = "No content metadata provided, nor content directories found for content_type: %s" % \
        content_meta.content_type
    raise exceptions.GalaxyClientError(msg)


# FIXME: mv to AnsibleGalaxyMetadata
def load_archive_metadata(tar_file_obj, galaxy_file, meta_file):
    galaxy_metadata = None
    metadata = None

    try:
        if galaxy_file:
            # Let the galaxy_file take precedence
            galaxy_metadata = content_repository.load(tar_file_obj.extractfile(galaxy_file))
        elif meta_file:
            metadata = yaml.safe_load(tar_file_obj.extractfile(meta_file))
    except Exception as e:
        log.warn('unable to extract and yaml load galaxy_file=%s meta_file=%s tar_file_obj=%s',
                 galaxy_file, meta_file, tar_file_obj)
        log.exception(e)

        # TODO: some archive specific exception
        raise exceptions.GalaxyClientError("this role does not appear to have a valid meta/main.yml or ansible-galaxy.yml file.")

    return galaxy_metadata, metadata


def tar_info_content_name_match(tar_info, content_name, content_path=None, match_pattern=None):
    # log.debug('tar_info=%s, content_name=%s, content_path=%s, match_pattern=%s',
    #          tar_info, content_name, content_path, match_pattern)
    # only reg files or symlinks can match
    if not tar_info.isreg() and not tar_info.islnk():
        return False

    content_path = content_path or ""

    # TODO: test cases for patterns
    if not match_pattern:
        match_pattern = '*%s*' % content_name

        if content_path:
            match_pattern = '*/%s/%s*' % (content_path, content_name)

    # log.debug('match_pattern=%s', match_pattern)
    # FIXME: would be better as two predicates both apply by comprehension
    if fnmatch.fnmatch(tar_info.name, match_pattern):
        return True

    return False


# ansible-galaxy.yml is based on fnmatch style patterns
def filter_members_by_fnmatch(tar_file_obj, match_pattern):
    tar_file_members = tar_file_obj.getmembers()

    member_matches = [tar_file_member for tar_file_member in tar_file_members
                      if fnmatch.fnmatch(tar_file_member.name, match_pattern)]

    return member_matches


def filter_members_by_content_type(tar_file_obj,
                                   content_meta):
    if not content_meta:
        log.debug('no content_meta info')
        return []

    content_type = content_meta.content_type

    tar_file_members = tar_file_obj.getmembers()

    member_matches = [tar_file_member for tar_file_member in tar_file_members
                      if tar_info_content_name_match(tar_file_member,
                                                     "",
                                                     # self.content_meta.name,
                                                     content_path=CONTENT_TYPE_DIR_MAP.get(content_type))]

    # everything for roles
    if content_type == 'role':
        member_matches = tar_file_members

    # log.debug('member_matches=%s', pprint.pformat([x.name for x in member_matches]))

    return member_matches


# FIXME: persisting of content archives or subsets thereof
# FIXME: currently does way too much, could be split into generic and special case classes
# FIXME: some weirdness here is caused by tarfile API being a little strange. To extract a file
#        to a different path than from the archive, you have to update each TarInfo member and
#        change it's 'name' attribute after loading/opening a TarFile() but before extract()
#        Since it's mutating the TarFile object, have to be careful if anything will use the object
#        after it was changed
# TODO: figure out content_type_requires_meta up a layer?
#          content_type != "role" and content_type not in self.NO_META:
def extract_by_content_type(tar_file_obj,
                            parent_dir,
                            content_meta,
                            file_name=None,
                            files_to_extract=None,
                            extract_to_path=None,
                            content_type=None,
                            display_callback=None,
                            install_all_content=False,
                            force_overwrite=False,
                            content_type_requires_meta=True):
    """
    Extract and write out files from the archive, this is a common operation
    needed for both old-roles and new-style galaxy content, the main
    difference is parent directory

    :param tar_file: tarfile, the local archive of the galaxy content files
    :param parent_dir: str, parent directory path to extract to
    :kwarg file_name: str, specific filename to extract from parent_dir in archive
    """
    # now we do the actual extraction to the path
    log.debug('tar_file=%s, parent_dir=%s, file_name=%s', tar_file_obj, parent_dir, file_name)
    log.debug('extract_to_path=%s', extract_to_path)
    log.debug('content_meta=%s', content_meta)

    display_callback = display_callback or default_display_callback
    files_to_extract = files_to_extract or []

    # if content_type != "role" and content_type not in self.NO_META:

    plugin_found = None

    if file_name:
        files_to_extract.append(file_name)
    # log.debug('files_to_extract: %s', files_to_extract)

    path = extract_to_path

    # append the content_dir if we have one
    content_sub_path = os.path.join(path, content_meta.content_dir or '')

    log.debug('path=%s', path)
    log.debug('conte_sub_path=%s', content_sub_path)
    # log.debug('files_to_extract=%s', pprint.pformat(files_to_extract))

    # do we need to drive this from tar_file members if we have file_names_to_extract?
    # for member in tar_file.getmembers():
    for member in files_to_extract:
        # Have to preserve this to reset it for the sake of processing the
        # same TarFile object many times when handling an ansible-galaxy.yml
        # file
        orig_name = member.name
        # log.debug('member.name=%s', member.name)
        # log.debug('member=%s, orig_name=%s, member.isreg()=%s member.issym()=%s',
        #               member, orig_name, member.isreg(), member.issym())
        # we only extract files, and remove any relative path
        # bits that might be in the file for security purposes
        # and drop any containing directory, as mentioned above
        # TODO: could we use tar_info_content_name_match with a '*' patter here to
        #       get a files_to_extract?
        if member.isreg() or member.issym():
            parts_list = member.name.split(os.sep)

            # filter subdirs if provided
            # Check if the member name (path), minus the tar
            # archive baseir starts with a subdir we're checking
            if file_name:
                # The parent_dir passed in when a file name is specified
                # should be the full path to the file_name as defined in the
                # ansible-galaxy.yml file. If that matches the member.name
                # then we've found our match.
                if member.name == os.path.join(parent_dir, file_name):
                    # lstrip content_meta.name because that's going to be the
                    # archive directory name and we don't need/want that
                    plugin_found = parent_dir.lstrip(content_meta.name)

            # secondary dir (roles/, callback_plugins/) is a match for the content_type
            elif len(parts_list) > 1 and parts_list[1] == CONTENT_TYPE_DIR_MAP.get(content_meta.content_type):
                plugin_found = CONTENT_TYPE_DIR_MAP.get(content_meta.content_type)



            # log.debug('plugin_found1: %s', plugin_found)
            # if not plugin_found:
            #    continue


            # TODO: This next two stanzas are building up the rel path name a file will use
            #       when it is extract (the 'extract_as' name). It is also updating the
            #       TarInfo.name to the new extract_as name
            #
            # TODO: extract this to a method that takes a list of TarInfo objects and returns
            #       a list of TarInfo objects with the member.name updated (and the orig name?).
            #       Ideally that would be a copy of the list instead of modifying it in place.
            #

            # log.debug('parts_list: %s', parts_list)
            # log.debug('plugin_found2: %s', plugin_found)

            # TODO: if we are doing one content_type at a time, seems like we can flatten this some
            if plugin_found:
                # If this is not a role, we don't expect it to be installed
                # into a subdir under roles path but instead directly
                # where it needs to be so that it can immediately be used
                #
                # FIXME - are galaxy content types namespaced? if so,
                #         how do we want to express their path and/or
                #         filename upon install?
                if plugin_found in parts_list:
                    # subdir_index = parts_list.index(plugin_found) + 1
                    subdir_index = parts_list.index(plugin_found) + 1
                    # log.debug('subdir_index: %s parts_list[subdir_index:]=%s', subdir_index, parts_list[subdir_index:])
                    parts = parts_list[subdir_index:]
                else:
                    # The desired subdir has been identified but the
                    # current member belongs to another subdir so just
                    # skip it
                    continue
            else:
                parts = member.name.replace(parent_dir, "", 1).split(os.sep)
                # log.debug('plugin_found falsey, building parts: %s', parts)

            # log.debug('parts: %s', parts)
            final_parts = []
            for part in parts:
                if part != '..' and '~' not in part and '$' not in part:
                    final_parts.append(part)
            member.name = os.path.join(*final_parts)

            # TODO: build the list of TarInfo members to extract and return it
            # TODO: The extract bits below move into sep method
            # log.debug('final_parts: %s', final_parts)
            # log.setLevel(logging.INFO)
            log.debug('member.name: %s', member.name)

            dest_path = os.path.join(content_sub_path, member.name)
            log.debug('path=%s, member.name=%s, dest_path=%s', path, member.name, dest_path)

            # display_callback("-- extracting %s content %s from %s into %s" %
            #                 (content_meta.content_type, member.name, content_meta.name, dest_path))

            if os.path.exists(dest_path) and not force_overwrite:
                message = (
                    "the specified Galaxy Content %s appears to already exist." % dest_path,
                    "Use of --force for non-role Galaxy Content Type is not yet supported"
                )
                raise exceptions.GalaxyClientError(" ".join(message))

            # Alright, *now* actually write the file
            log.debug('Extracting member=%s, path=%s', member, path)
            tar_file_obj.extract(member, path)

            # log.setLevel(logging.DEBUG)
            # Reset the name so we're on equal playing field for the sake of
            # re-processing this TarFile object as we iterate through entries
            # in an ansible-galaxy.yml file
            member.name = orig_name

    if content_type_requires_meta:
        if not plugin_found:



            log.warn('we dont think we found a meta/main.yml but we probably did, fixme')


            # raise exceptions.GalaxyClientError("Required subdirectory not found in Galaxy Content archive for %s" % content_meta.name)
