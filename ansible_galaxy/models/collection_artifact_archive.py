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


@attr.s(frozen=True)
class CollectionArtifactArchive(RepositoryArchive):
    pass
