# attempt to abstract (tar) archive handling a bit

# would like a easy way to extract a subdir of a tar archive to
# a directory on local fs while using relative paths

import fnmatch
import logging
import os


from ansible_galaxy import exceptions
from ansible_galaxy.models.content import CONTENT_TYPE_DIR_MAP, CONTENT_PLUGIN_TYPES

log = logging.getLogger(__name__)

# pass in list of tarinfo of paths to extract
# pass in a map of tar member paths -> dest paths, built separately?
#  (based on content_type and CONTENT_TYPE_DIR_MAP etc)


def default_display_callback(*args, **kwargs):
    log.debug('args=%s, kwargs=%s', args, kwargs)

    print(args, kwargs)

# for plugins and everything except roles
# extract_content_by_content_type(content_type, base_path=None)

# for roles
# extract_content_by_role_name(role_name)

# def content_type_match(content_type, member_path):


# TODO:

def tar_info_content_name_match(tar_info, content_name, content_path=None):
    log.debug('tar_info=%s, content_name=%s, content_path=%s',
              tar_info, content_name, content_path)
    # only reg files or symlinks can match
    if not tar_info.isreg() and not tar_info.islnk():
        return False

    content_path = content_path or ""

    # TODO: test cases for patterns
    match_pattern = '*%s*' % content_name
    if content_path:
        match_pattern = '*/%s/%s*' % (content_path, content_name)

    log.debug('match_pattern=%s', match_pattern)
    # FIXME: would be better as two predicates both apply by comprehension
    if fnmatch.fnmatch(tar_info.name, match_pattern):
        return True

    return False


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
                                                     content_path=CONTENT_TYPE_DIR_MAP[content_type])]

    log.debug('member_matches=%s', member_matches)

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

    display_callback = display_callback or default_display_callback
    files_to_extract = files_to_extract or []

    # if content_type != "role" and content_type not in self.NO_META:

    plugin_found = None

    if file_name:
        files_to_extract.append(file_name)
    # log.debug('files_to_extract: %s', files_to_extract)

    path = extract_to_path
    log.debug('path=%s', path)
    log.debug('files_to_extract=%s', files_to_extract)
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
            elif len(parts_list) > 1 and parts_list[1] == CONTENT_TYPE_DIR_MAP[content_meta.content_type]:
                plugin_found = CONTENT_TYPE_DIR_MAP[content_meta.content_type]

            # log.debug('plugin_found1: %s', plugin_found)
            if not plugin_found:
                continue

            # log.debug('parts_list: %s', parts_list)
            # log.debug('plugin_found2: %s', plugin_found)
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

            # log.debug('final_parts: %s', final_parts)
            log.debug('member.name: %s', member.name)

            display_callback(
                "-- extracting %s %s from %s into %s" %
                (content_meta.content_type, member.name, content_meta.name, os.path.join(path, member.name))
            )

            if os.path.exists(os.path.join(path, member.name)) and not force_overwrite:
                message = (
                    "the specified Galaxy Content %s appears to already exist." % os.path.join(path, member.name),
                    "Use of --force for non-role Galaxy Content Type is not yet supported"
                )
                raise exceptions.GalaxyClientError(" ".join(message))

            # Alright, *now* actually write the file
            log.debug('Extracting member=%s, path=%s', member, path)
            tar_file_obj.extract(member, path)

            # Reset the name so we're on equal playing field for the sake of
            # re-processing this TarFile object as we iterate through entries
            # in an ansible-galaxy.yml file
            member.name = orig_name

    if content_type_requires_meta:
        if not plugin_found:
            raise exceptions.GalaxyClientError("Required subdirectory not found in Galaxy Content archive for %s" % content_meta.name)
