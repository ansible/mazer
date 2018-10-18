# attempt to abstract (tar) archive handling a bit

# would like a easy way to extract a subdir of a tar archive to
# a directory on local fs while using relative paths

import fnmatch
import logging
import os

from ansible_galaxy import exceptions
from ansible_galaxy.models import content

log = logging.getLogger(__name__)

# pass in list of tarinfo of paths to extract
# pass in a map of tar member paths -> dest paths, built separately?
#  (based on content_type and content.CONTENT_TYPE_DIR_MAP etc)

# for plugins and everything except roles
# extract_content_by_content_type(content_type, base_path=None)

# for roles
# extract_content_by_role_name(role_name)

# def content_type_match(content_type, member_path):


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
def filter_members_by_fnmatch(tar_file_members, match_pattern):

    member_matches = [tar_file_member for tar_file_member in tar_file_members
                      if fnmatch.fnmatch(tar_file_member.name, match_pattern)]

    return member_matches


def filter_members_by_content_type(tar_file_members,
                                   content_archive_type,
                                   content_type):

    member_matches = [tar_file_member for tar_file_member in tar_file_members
                      if tar_info_content_name_match(tar_file_member,
                                                     "",
                                                     # self.content_meta.name,
                                                     content_path=content.CONTENT_TYPE_DIR_MAP.get(content_type))]

    # everything for roles
    if content_archive_type == 'role':
        member_matches = tar_file_members

    # log.debug('member_matches=%s', pprint.pformat([x.name for x in member_matches]))

    return member_matches


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
    dest_path = os.path.join(dest_dir, dest_filename)
    log.debug('dest_dir: %s, dest_filename: %s, dest_path: %s orig_name: %s',
              dest_dir, dest_filename, dest_path, orig_name)
    if os.path.exists(dest_path):
        if not force_overwrite:
            message = "The Galaxy content %s appears to already exist." % dest_path
            raise exceptions.GalaxyClientError(message)

    try:
        tar_file.getmember(archive_member.name)
    except KeyError:
        raise exceptions.GalaxyArchiveError('The archive "%s" has no file "%s"' % (tar_file.name, archive_member.name),
                                            archive_path=tar_file.name)

    # TODO: set a default owner/group
    # MAYBE TODO: pick a 'install time' and make sure all the mtime/ctime values of extracted files
    #             match the 'install time' used in .galaxy_install_info ?

    # change the tar file member name in place to just the filename ('myfoo.py') so that extract places that file in
    # dest_dir directly instead of using adding the archive path as well
    # like '$dest_dir/archive-roles/library/myfoo.py'
    archive_member.name = dest_filename

    # log.debug('tar member: %s dest_dir: %s', archive_member, dest_dir)
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
