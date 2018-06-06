# attempt to abstract (tar) archive handling a bit

# would like a easy way to extract a subdir of a tar archive to
# a directory on local fs while using relative paths

import fnmatch
import logging
import os
import yaml


from ansible_galaxy import exceptions
from ansible_galaxy.models.content import CONTENT_TYPE_DIR_MAP, CONTENT_TYPES
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
APB_YAML = 'apb.yml'


class ContentArchiveMetadataFiles(object):
    def __init__(self):
        self.meta_main_yml = None
        self.meta_main_parent_dir = None

        self.galaxy_file = None
        self.apb_yaml = None

        # FIXME: doesnt belong here
        self.archive_parent_dir = None


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

    apb_yaml_file = None

    for member in archive_members:
        if fnmatch.fnmatch(member.name, '*/%s' % APB_YAML):
            log.debug('apb.yml member: %s', member)
            apb_yaml_file = member.name

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

    log.debug('apb_yaml_file: %s', apb_yaml_file)
    # FIXME: return a real type/object for archive metadata
    return (meta_file,
            meta_parent_dir,
            galaxy_file,
            apb_yaml_file)


def find_archive_parent_dir(archive_members, content_type, content_dir):
    # archive_parent_dir wasn't found when checking for metadata files
    archive_parent_dir = None

    shortest_dir = None
    for member in archive_members:
        # This is either a new-type Galaxy Content that doesn't have an
        # ansible-galaxy.yml file and the type desired is specified and
        # we check parent dir based on the correct subdir existing or
        # we need to just scan the subdirs heuristically and figure out
        # what to do
        member_dir = os.path.dirname(os.path.dirname(member.name))
        shortest_dir = shortest_dir or member_dir

        if len(member_dir) < len(shortest_dir):
            shortest_dir = member_dir

        if content_type != "all":
            if content_dir and content_dir in member.name:
                archive_parent_dir = os.path.dirname(member.name)
                return archive_parent_dir
        else:
            for plugin_dir in CONTENT_TYPE_DIR_MAP.values():
                if plugin_dir in member.name:
                    archive_parent_dir = os.path.dirname(member.name)
                    return archive_parent_dir

    if content_type not in CONTENT_TYPES:
        log.debug('did not find a content_dir or plugin_dir, so using shortest_dir %s for archive_parent_dir', shortest_dir)
        return shortest_dir

    # TODO: archive format exception?
    msg = "No content metadata provided, nor content directories found for content_type: %s" % \
        content_type
    log.debug('content_type: %s', content_type)
    log.debug('content_dir: %s', content_dir)
    raise exceptions.GalaxyClientError(msg)


# FIXME: mv to AnsibleGalaxyMetadata
def load_archive_role_metadata(tar_file_obj, meta_file_path):
    metadata = None
    if not meta_file_path:
        return None

    try:
        metadata = yaml.safe_load(tar_file_obj.extractfile(meta_file_path))
    except Exception:
        log.debug('unable to extract and yaml load role meta_file=%s tar_file_obj=%s',
                  meta_file_path, tar_file_obj)

    return metadata


def load_archive_galaxyfile(tar_file_obj, galaxy_file_path):
    galaxy_metadata = None
    if not galaxy_file_path:
        return None

    try:
        galaxy_metadata = content_repository.load(tar_file_obj.extractfile(galaxy_file_path))
    except Exception:
        log.warn('unable to extract and yaml load galaxy_file=%s tar_file_obj=%s',
                 galaxy_file_path, tar_file_obj)

    return galaxy_metadata


def load_archive_apb_yaml(tar_file_obj, apb_yaml_path):
    apb_data = None
    if not apb_yaml_path:
        return None

    try:
        apb_data = yaml.safe_load(tar_file_obj.extractfile(apb_yaml_path))
    except Exception:
        log.warn('unable to extract and yaml load apb_yaml_path=%s tar_file_obj=%s',
                 apb_yaml_path, tar_file_obj)

    return apb_data


# FIXME: causes issues on py3
# suppose we could make this a generator if needed
def find_content_type_subdirs(tar_file_members):
    '''Return a list of content type subdirs found in tar_file_members

    This list comprehension will iterate every member entry in
    the tarfile, split it's name by os.sep and drop the top most
    parent dir, which will be self.content_meta.name (we don't want it as it's
    not needed for plugin types. First make sure the length of
    that split and drop of parent dir is length > 1 and verify
    that the subdir is infact in CONTENT_TYPE_DIR_MAP.values()

    This should give us a list of valid content type subdirs
    found heuristically within this Galaxy Content repo'''
    plugin_subdirs = [
        os.path.join(m.name.split(os.sep)[1:])[0]
        for m in tar_file_members
        if len(os.path.join(m.name.split(os.sep)[1:])) > 1
        and os.path.join(m.name.split(os.sep)[1:])[0] in CONTENT_TYPE_DIR_MAP.values()
    ]

    # uniq and order
    plugin_subdirs_set = set(plugin_subdirs)
    return sorted(list(plugin_subdirs_set))


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
                                   content_archive_type,
                                   content_type):

    tar_file_members = tar_file_obj.getmembers()

    member_matches = [tar_file_member for tar_file_member in tar_file_members
                      if tar_info_content_name_match(tar_file_member,
                                                     "",
                                                     # self.content_meta.name,
                                                     content_path=CONTENT_TYPE_DIR_MAP.get(content_type))]

    # everything for roles
    if content_archive_type == 'role':
        member_matches = tar_file_members

    # log.debug('member_matches=%s', pprint.pformat([x.name for x in member_matches]))

    return member_matches


def filter_members_by_content_meta(tar_file_obj, content_archive_type, content_meta):
    if not content_meta:
        log.debug('no content_meta info')
        return []

    content_type = content_meta.content_type

    return filter_members_by_content_type(tar_file_obj, content_archive_type, content_type)


def extract_file(tar_file, file_to_extract):
    # TODO: should just be a object? ContentArchiveMember? ContentArchiveExtractData ?
    archive_member = file_to_extract['archive_member']
    dest_dir = file_to_extract['dest_dir']
    dest_filename = file_to_extract['dest_filename']
    force_overwrite = file_to_extract['force_overwrite']

    orig_name = archive_member.name
    if not archive_member.isreg() and not archive_member.issym():
        return None

    # TODO: raise from up a level in the stack?
    # if os.path.exists(extract_to_path):
    #    if not force_overwrite:
    #        message = "The Galaxy content %s appears to already exist." % extract_to_path
    #        raise exceptions.GalaxyClientError(message)

    # change the tar file member name in place to just the filename ('myfoo.py') so that extract places that file in
    # dest_dir directly instead of using adding the archive path as well
    # like '$dest_dir/archive-roles/library/myfoo.py'
    archive_member.name = dest_filename
    tar_file.extract(archive_member, dest_dir) 


    installed_path = os.path.join(dest_dir, dest_filename)

    # reset the tar info object's name attr to the origin value in
    # case something else references this
    archive_member.name = orig_name
    return installed_path


def extract_files(tar_file, files_to_extract):
    '''Process tar_file, extracting the files from files_to_extract'''

    for file_to_extract in files_to_extract:
        res = extract_file(tar_file, file_to_extract)
        if res:
            yield res


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
                            display_callback=None,
                            force_overwrite=False):
    """
    Extract and write out files from the archive, this is a common operation
    needed for both old-roles and new-style galaxy content, the main
    difference is parent directory

    Returns a list of files that were installed.

    :param tar_file: tarfile, the local archive of the galaxy content files
    :param parent_dir: str, parent directory path to extract to
    :kwarg file_name: str, specific filename to extract from parent_dir in archive
    """

    installed_paths = []
    overwritten_paths = []

    # parent_dir = parent_dir or tar_file_obj.members
    # details of archive extraction, pretty verbose even for debug
    elog = logging.getLogger('%s.(extract)' % __name__)

    # now we do the actual extraction to the
    elog.debug('tar_file=%s, parent_dir=%s, file_name=%s', tar_file_obj, parent_dir, file_name)
    elog.debug('extract_to_path=%s', extract_to_path)
    elog.debug('content_meta=%s', content_meta)

    display_callback = display_callback or default_display_callback
    files_to_extract = files_to_extract or []

    # if content_type != "role" and content_type not in self.NO_META:

    plugin_found = None

    if file_name:
        files_to_extract.append(file_name)
    # log.debug('files_to_extract: %s', files_to_extract)

    # path = extract_to_path

    # append the content_dir if we have one
    content_path = os.path.join(extract_to_path,
                                CONTENT_TYPE_DIR_MAP.get('install_content_type', content_meta.content_dir or ''))
    if content_meta.content_sub_dir:
        log.debug('content_sub_path=%s', content_meta.content_sub_dir)
        content_path = os.path.join(content_path, content_meta.content_sub_dir or '')

    log.debug('extract_to_path=%s', extract_to_path)
    log.debug('content_path=%s', content_path)

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
            # FIXME: plugin_found isnt a great name, really just a var to track if we found the type
            #        of content we are looking for
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
                parts = []
                if parent_dir:
                    parts = member.name.replace(parent_dir, "", 1).split(os.sep)
                elog.debug('plugin_found falsey, building parts: %s', parts)

            # log.debug('parts: %s', parts)
            final_parts = []
            for part in parts:
                if part != '..' and '~' not in part and '$' not in part:
                    final_parts.append(part)

            elog.debug('final_parts: %s', final_parts)
            elog.debug('orig member.name: %s', member.name)

            if final_parts:
                member.name = os.path.join(*final_parts)

            elog.debug('new  member.name: %s', member.name)

            # TODO: build the list of TarInfo members to extract and return it
            # TODO: The extract bits below move into sep method
            # log.debug('member.name: %s', member.name)

            dest_path = os.path.join(content_path, member.name)

            elog.debug('extract_to_path=%s', extract_to_path)
            elog.debug('member.name=%s', member.name)
            elog.debug('dest_path=%s', dest_path)

            # display_callback("-- extracting %s content %s from %s into %s" %
            #                 (content_meta.content_type, member.name, content_meta.name, dest_path))

            if os.path.exists(dest_path):
                if not force_overwrite:
                    message = "The Galaxy content %s appears to already exist." % dest_path
                    raise exceptions.GalaxyClientError(message)

                overwritten_paths.append(dest_path)

            # Alright, *now* actually write the file
            elog.debug('Extracting member=%s, content_path=%s', member, content_path)
            tar_file_obj.extract(member, content_path)

            # installed_path = os.path.join(path, member.name)
            installed_path = os.path.join(content_path, member.name)
            installed_paths.append(installed_path)
            # Reset the name so we're on equal playing field for the sake of
            # re-processing this TarFile object as we iterate through entries
            # in an ansible-galaxy.yml file
            member.name = orig_name

    if content_meta.requires_meta_main:
        if not plugin_found:
            log.warn('%s requires a meta/main.yml but we didnt find one', content_meta.name)
            # raise exceptions.GalaxyClientError("Required subdirectory not found in Galaxy Content archive for %s" % content_meta.name)

    elog.debug('Installed paths: %s', installed_paths)

    if overwritten_paths:
        elog.debug('Some content that already existed was overwritten because force_overwrite=%s: %s',
                   force_overwrite, sorted(overwritten_paths))

    return installed_paths
