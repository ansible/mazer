import attr


@attr.s(frozen=True)
class ContentArchiveInfo(object):
    requires_meta_main = False

    archive_type = attr.ib()
    top_dir = attr.ib()
    archive_path = attr.ib(default=None)

    # download url?
    # file path?
    # checksum?
    # signature?


@attr.s(frozen=True)
class ContentArchive(object):
    # Can be created from a collection archive, a collection artifact archive,
    # or a trad role archive, or a trad role archive artifact.
    info = attr.ib(type=ContentArchiveInfo)
