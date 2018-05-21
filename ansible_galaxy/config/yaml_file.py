import logging
import os
import yaml

import yamlloader

log = logging.getLogger(__name__)

CONFIG_FILE = '~/.ansible/galaxy.yml'


def config_save(conf_data, file_path=None):
    file_path = file_path or CONFIG_FILE
    full_file_path = os.path.expanduser(file_path)

    with open(full_file_path, 'w+') as config_file:
        yaml.dump(conf_data,
                  config_file,
                  Dumper=yamlloader.ordereddict.CSafeDumper,
                  default_flow_style=False)


def config_load(file_path=None):
    file_path = file_path or CONFIG_FILE
    full_file_path = os.path.expanduser(file_path)

    with open(full_file_path, 'r') as config_file:
        conf_data = yaml.load(config_file,
                              Loader=yamlloader.ordereddict.CSafeLoader)
        log.debug('conf_data: %s', conf_data)
        return conf_data
