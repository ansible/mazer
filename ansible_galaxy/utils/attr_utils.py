import logging
import pprint

import attr
from attr.exceptions import NotAnAttrsClassError

import six

log = logging.getLogger(__name__)


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
