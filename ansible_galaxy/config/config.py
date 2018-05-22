import collections
import logging

from ansible_galaxy.config import defaults
from ansible_galaxy.config import config_file

log = logging.getLogger(__name__)


class Config(object):
    def __init__(self):
        self.server = {}
        self.content_path = None
        self.options = {}

    def as_dict(self):
        return collections.OrderedDict([
                ('server', self.server),
                ('content_path', self.content_path),
                ('options', self.options),
        ])

    @classmethod
    def from_dict(cls, data):
        inst = cls()
        inst.server = data.get('server', inst.server)
        inst.content_path = data.get('content_path', inst.content_path)
        inst.options = data.get('options', inst.options)
        return inst


def load(full_file_path):
    '''Load the yaml config file at full_file_path and create and return an instance of Config'''
    config_file_data = config_file.load(full_file_path)

    _default_conf_data = collections.OrderedDict(defaults.DEFAULTS)

    config_data = config_file_data or _default_conf_data

    log.debug('config_data: %s', config_data)

    return Config.from_dict(config_data)


def save(config_obj, full_file_path):
    '''Save an instance of Config (config_obj) to full_file_path'''

    config_data = config_obj.as_dict()

    return config_file.save(config_data, full_file_path)
