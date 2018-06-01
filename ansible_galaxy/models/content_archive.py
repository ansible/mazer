

class ContentArchiveMeta(object):
    _archive_type = None
    requires_meta_main = False

    def __init__(self, archive_type=None, archive_path=None, top_dir=None):
        self.archive_type = archive_type or self._archive_type
        self.top_dir = top_dir
        self.archive_path = archive_path

    # download url?
    # file path?
    # checksum?
    # signature?


class RoleContentArchiveMeta(ContentArchiveMeta):
    _archive_type = 'role'
    requires_meta_main = True
