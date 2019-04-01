import tarfile

import attr


# TODO: I think we may be able to get rid of this class entirely
#       archive_type, top_dir, requires_meta_main at least are unused
@attr.s(frozen=True)
class CollectionArtifactArchiveInfo(object):
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
