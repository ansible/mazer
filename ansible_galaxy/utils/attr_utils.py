import logging
import pprint

import attr
from attr.exceptions import NotAnAttrsClassError

import six

log = logging.getLogger(__name__)


def convert_none_to_empty_dict(val):
    ''' if val is None, return an empty dict'''

    # if val is not a dict or val 'None' return val
    # and let the validators raise errors later
    if val is None:
        return {}
    return val


def convert_single_to_list(val):
    '''If a single object is provided, replace with a list containing only that object'''

    if val is None:
        return []

    if not isinstance(val, list):
        return [val]

    return val


def is_attr(obj):
    if isinstance(obj, six.class_types):
        try:
            attr.fields(obj)
        except NotAnAttrsClassError:
            return False
        return False

    if getattr(obj.__class__, "__attrs_attrs__", None):
        return True

    if getattr(obj, "__attrs_attrs__", None):
        return True

    return False


def pf_attr(obj):
    if not is_attr(obj):
        return pprint.pformat(obj)

    return pprint.pformat(attr.fields_dict(obj))
