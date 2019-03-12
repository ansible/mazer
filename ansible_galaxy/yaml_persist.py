from collections import OrderedDict
import logging
import os

import attr
import yaml

from ansible_galaxy.utils import attr_utils

log = logging.getLogger(__name__)


class MazerSafeDumper(yaml.SafeDumper):
    '''A Yaml dumper that dumps more or less ansible-style

    ie, two space indent on lists always, flow_style=False
    on mappings

    Also adds support for OrderedDict'''
    def increase_indent(self, flow=False, indentless=False):
        return super(MazerSafeDumper, self).increase_indent(flow, False)

    def represent_data(self, data):
        '''Attempt to detect attrs style objects and convert to dicts

        We can't add a regular yaml_representer because attrs based objects can
        be of any type, so we need to detect if 'data' is attrs based (with
        attr_utils.is_attrs()) and if so, we covert it to an OrdedDict and
        then rely on the OrderedDict representer to dump the correct yaml.

        If this is anything other than an attrs based instance, we call
        super's represent_data()

        Also setup some representers with the default styles are 'ansible-style'
        for maps/dicts/lists/tuples
        '''

        if attr_utils.is_attr(data):
            odict = attr.asdict(data, recurse=True, dict_factory=OrderedDict)
            return super(MazerSafeDumper, self).represent_data(odict)

        return super(MazerSafeDumper, self).represent_data(data)


def dict_representer(dumper, data):
    return dumper.represent_mapping(u'tag:yaml.org,2002:map', data, flow_style=False)


def odict_representer(dumper, data):
    return dumper.represent_mapping(u'tag:yaml.org,2002:map', data.items(), flow_style=False)


def list_representer(dumper, data):
    return dumper.represent_sequence(u'tag:yaml.org,2002:seq', data, flow_style=False)


MazerSafeDumper.add_representer(OrderedDict, odict_representer)
MazerSafeDumper.add_representer(dict, dict_representer)
MazerSafeDumper.add_representer(list, list_representer)
MazerSafeDumper.add_representer(tuple, list_representer)


def safe_dump(data, stream=None, **kwargs):
    return yaml.dump(data, stream=stream, Dumper=MazerSafeDumper, **kwargs)


def load_from_filename(filename, load_method):
    if not os.path.isfile(filename):
        return None

    try:
        f = open(filename, 'r')
        return load_method(f)
    except Exception as e:
        log.exception(e)
        log.debug('Unable to load install info from path: %s', filename)
        return False
    finally:
        f.close()


def save(data, filename):
    log.debug('saving data to %s', filename)
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))

    with open(filename, 'w+') as f:
        # FIXME: just return the install_info dict (or better, build it elsewhere and pass in)
        # FIXME: stop minging self state
        try:
            install_info_ = safe_dump(data, stream=f)
        except Exception as e:
            log.warning('unable to serialize data to filename=%s for data=%s', filename, install_info_)
            log.exception(e)
            return False

    log.debug('wrote data to %s', filename)
    return True
