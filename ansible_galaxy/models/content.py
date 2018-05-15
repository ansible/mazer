
VALID_ROLE_SPEC_KEYS = [
    'src',
    'version',
    'role',
    'name',
    'scm',
]

# FIXME - need some stuff here
VALID_CONTENT_SPEC_KEYS = [

]


# Galaxy Content Constants
CONTENT_PLUGIN_TYPES = (
    'module', 'module_util', 'action_plugin', 'filter_plugin',
    'connection_plugin', 'inventory_plugin', 'lookup_plugin',
    'shell_plugin', 'strategy_plugin', 'netconf_plugin'

)
CONTENT_TYPES = CONTENT_PLUGIN_TYPES + ('role',)

CONTENT_TYPE_DIR_MAP = dict([(k, '%ss' % k) for k in CONTENT_TYPES])
CONTENT_TYPE_DIR_MAP['module'] = 'library'
TYPE_DIR_CONTENT_TYPE_MAP = dict([('%ss' % k, k) for k in CONTENT_TYPES])
TYPE_DIR_CONTENT_TYPE_MAP['library'] = 'module'


class GalaxyContentMeta(object):
    def __init__(self, name=None, version=None,
                 src=None, scm=None, content_type=None,
                 path=None, content_dir=None, content_sub_dir=None):
        self.name = name
        self.version = version
        self.src = src or name
        self.scm = scm
        self.content_type = content_type
        self.content_dir = content_dir
        self.content_sub_dir = content_sub_dir
        self.path = path

        self._data = {}

    @classmethod
    def from_data(cls, data):
        inst = cls(**data)
        return inst

    def __eq__(self, other):
        return (self.name, self.version, self.src, self.scm,
                self.content_type, self.content_dir, self.path) == \
            (other.name, other.version, other.src, other.scm,
             other.content_type, other.content_dir, other.path)

    def __repr__(self):
        return 'GalaxyContentMeta(name=%s, version=%s, src=%s, scm=%s, content_type=%s, content_dir=%s, content_sub_dir=%s, path=%s)' \
            % (self.name, self.version, self.src, self.scm, self.content_type, self.content_dir, self.content_sub_dir, self.path)

    def _as_dict(self):
        return {'name': self.name,
                'version': self.version,
                'src': self.src,
                'scm': self.scm,
                'content_type': self.content_type,
                'content_dir': self.content_dir,
                'content_sub_dir': self.content_sub_dir,
                'path': self.path}

    @property
    def data(self):
        self._data.update(self._as_dict())
        return self._data


class GalaxyContent(object):
    def __init__(self):
        # need class for obj for ansible-galaxy.yml metadata file
        self.galaxy_metadata = {}
        # or instance of some InstallInfo class
        self.install_info = {}
        # or instance of GalaxyContentMeta
        self.content_meta = {}
