from collections import OrderedDict
import logging

from ansible_galaxy import yaml_persist
from ansible_galaxy.models.collection_info import CollectionInfo

log = logging.getLogger(__name__)


test_dict = {'blip': 1,
             'bar': [{'a': 'A', 'b': 'B', 'cc': [None, 1, 2.3, ('blip', 'foo')]},
                     {'other': 'stuff'}],
             'somelists': [
                 [11, 12, 13, 14],
                 [555, 1.1, ['x', 't', 'z']],
             ],
             'somedicts': {'some_o_dict': OrderedDict({'3a': '3A', '3b': '3B'}),
                           'level2': {'ccvb': 'bcvvvv'},
                           'level3': {'hfgfg': '4e56'},
                           },
             'a_tuple': ('j', 'k', 'l', 'm'),
             }


def test_safe_dump():
    yaml_str = yaml_persist.safe_dump(test_dict)
    log.debug('yaml_str:\n%s', yaml_str)

    assert yaml_str is not None
    assert 'somedicts' in yaml_str


def test_safe_dump_attr():
    col_info = CollectionInfo(namespace='some_ns',
                              name='some_name',
                              version='1.2.3',
                              license='MIT',
                              description='stuff',
                              authors=['Charles Oakley'],
                              tags=['sometag', 'anothertag'],
                              dependencies=OrderedDict([('foo.bar', '*'),
                                                        ('blip.bar', '>=1.1.0')]))

    log.debug('col_info: %s', col_info)
    yaml_str = yaml_persist.safe_dump(col_info)
    log.debug('yaml_str:\n%s', yaml_str)

    assert yaml_str is not None
    assert 'blip.bar' in yaml_str
