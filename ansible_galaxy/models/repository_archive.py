import os
import tarfile

import attr


@attr.s(frozen=True)
class RepositoryArchiveInfo(object):
    requires_meta_main = False

    archive_type = attr.ib()
    top_dir = attr.ib()
    archive_path = attr.ib(default=None)

    # download url?
    # file path?
    # checksum?
    # signature?


@attr.s(frozen=True)
class RepositoryArchive(object):
    info = attr.ib(type=RepositoryArchiveInfo)
    tar_file = attr.ib(type=tarfile.TarFile, default=None)

    META_INSTALL = os.path.join('meta', '.galaxy_install_info')

    def repository_dest_root_subpath(self, repository_name):
        '''The relative path inside the installed content where extract should consider the root

        A collection archive for 'my_namespace.my_content' will typically be extracted to
        '~/.ansible/content/my_namespace/my_content' in which case the repository_dest_root_subpath
        should return just '/'.

        But Role archives will be extracted into a 'roles' sub dir of the typical path.
        ie, a 'my_namespace.my_role' role archive will need to be extracted to
        '~/.ansible/content/my_namespace/roles/my_role/' in which case the repository_dest_root_subpatch
        should return 'roles/my_roles' (ie, 'roles/%s' % content_name)
        '''
        return ''


@attr.s(frozen=True)
class TraditionalRoleRepositoryArchive(RepositoryArchive):
    ROLES_SUBPATH = 'roles'

    def repository_dest_root_subpath(self, repository_name):
        '''Traditional role archive repository gets installed into subpath of 'roles/CONTENT_NAME/'''
        return os.path.join(self.ROLES_SUBPATH, repository_name)


@attr.s(frozen=True)
class CollectionRepositoryArchive(RepositoryArchive):
    pass


@attr.s(frozen=True)
class CollectionRepositoryArtifactArchive(RepositoryArchive):
    pass
