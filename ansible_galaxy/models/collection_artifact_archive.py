import tarfile

import attr


@attr.s(frozen=True)
class CollectionArtifactArchiveInfo(object):
    requires_meta_main = False

    archive_type = attr.ib()
    top_dir = attr.ib()
    archive_path = attr.ib(default=None)

    # download url?
    # file path?
    # checksum?
    # signature?


@attr.s(frozen=True)
class CollectionArtifactArchive(object):
    info = attr.ib(type=CollectionArtifactArchiveInfo)
    tar_file = attr.ib(type=tarfile.TarFile, default=None)
