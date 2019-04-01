# attempt to abstract (tar) archive handling a bit

# would like a easy way to extract a subdir of a tar archive to
# a directory on local fs while using relative paths

import logging
import os

from ansible_galaxy import exceptions

log = logging.getLogger(__name__)


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
    # log.debug('dest_dir: %s, dest_filename: %s, dest_path: %s orig_name: %s',
    #          dest_dir, dest_filename, dest_path, orig_name)
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
