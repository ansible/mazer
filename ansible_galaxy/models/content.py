import logging

log = logging.getLogger(__name__)


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
    'module',
    'module_util',
    'action_plugin',
    'apb',
    'filter_plugin',
    'connection_plugin',
    'inventory_plugin',
    'lookup_plugin',
    'shell_plugin',
    'strategy_plugin',
    'netconf_plugin',
    'callback_plugin',
)
CONTENT_TYPES = CONTENT_PLUGIN_TYPES + ('role',)
SUPPORTED_CONTENT_TYPES = ('role',)

CONTENT_TYPE_DIR_MAP = dict([(k, '%ss' % k) for k in CONTENT_TYPES])
CONTENT_TYPE_DIR_MAP['module'] = 'library'
TYPE_DIR_CONTENT_TYPE_MAP = dict([('%ss' % k, k) for k in CONTENT_TYPES])
TYPE_DIR_CONTENT_TYPE_MAP['library'] = 'module'


class GalaxyContentMeta(object):
    def __init__(self, name=None, version=None,
                 src=None, scm=None,
                 content_type=None,
                 path=None, requires_meta_main=None,
                 content_dir=None, content_sub_dir=None,
                 namespace=None):

        self.name = name
        self.version = version
        self.src = src or name
        self.scm = scm
        self.content_type = content_type
        self.path = path
        self.requires_meta_main = requires_meta_main
        self.content_dir = content_dir
        self.content_sub_dir = content_sub_dir
        self.namespace = namespace
        self._data = {}


#         log.debug('%s locals: %s', self.__class__.__name__, locals())

    @classmethod
    def from_data(cls, data):
        inst = cls(**data)
        return inst

    def __eq__(self, other):
        return (self.name, self.namespace, self.version, self.src, self.scm,
                self.content_type, self.content_dir, self.path) == \
            (other.name, other.namespace, other.version, other.src, other.scm,
             other.content_type, other.content_dir, other.path)

    def __repr__(self):
        format_ = 'GalaxyContentMeta(name=%s, namespace=%s, version=%s, src=%s, scm=%s, ' + \
            'content_type=%s, content_dir=%s, content_sub_dir=%s, path=%s, requires_meta_main=%s)'

        return format_ % (self.name, self.namespace, self.version, self.src, self.scm,
                          self.content_type, self.content_dir, self.content_sub_dir,
                          self.path, self.requires_meta_main)

    def _as_dict(self):
        return {'name': self.name,
                'namespace': self.namespace,
                'version': self.version,
                'src': self.src,
                'scm': self.scm,
                'content_type': self.content_type,
                'path': self.path,
                'requires_meta_main': self.requires_meta_main,
                'content_dir': self.content_dir,
                'content_sub_dir': self.content_sub_dir,
                }

    @property
    def data(self):
        self._data.update(self._as_dict())
        return self._data


# TODO: separate GalaxyContent, ContentMeta and ContentArchive classes
class RoleContentMeta(GalaxyContentMeta):

    def __init__(self, *args, **kwargs):
        super(RoleContentMeta, self).__init__(*args, **kwargs)
        self.content_type = 'role'
        self.content_dir = CONTENT_TYPE_DIR_MAP.get('role', None)
        self.content_sub_dir = self.name

        # self.requires_meta_main = True
        log.debug('%s self.__dict__: %s', self.__class__.__name__, self.__dict__)


class APBContentArchiveMeta(GalaxyContentMeta):
    def __init__(self, *args, **kwargs):
        apb_data = kwargs.pop('apb_data', {})
        super(APBContentArchiveMeta, self).__init__(*args, **kwargs)

        self.apb_data = apb_data
        self.content_type = 'apb'
        self.content_dir = CONTENT_TYPE_DIR_MAP.get('apb', None)
        self.content_sub_dir = self.apb_data.get('name', self.name)


class GalaxyContent(object):
    def __init__(self):
        # need class for obj for ansible-galaxy.yml metadata file
        self.galaxy_metadata = {}
        # or instance of some InstallInfo class
        self.install_info = {}
        # or instance of GalaxyContentMeta
        self.content_meta = {}
