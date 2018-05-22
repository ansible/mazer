import logging
import yaml

import yamlloader

log = logging.getLogger(__name__)


def load(config_file_stream):
    conf_data = yaml.load(config_file_stream,
                          Loader=yamlloader.ordereddict.CSafeLoader)
    return conf_data


def save(conf_data, config_file_stream):
    result = yaml.dump(conf_data,
                       config_file_stream,
                       Dumper=yamlloader.ordereddict.CSafeDumper,
                       default_flow_style=False)
    return result
