
# -*- coding: utf-8 -*-
from __future__ import print_function

import logging
import re

import attr
import semantic_version
import six

from ansible_galaxy.data import spdx_licenses

log = logging.getLogger(__name__)

TAG_REGEXP = re.compile('^[a-z0-9]+$')

# match only lowercase alphanumerics or underscore without
# leading numbers or underscores or multiple consecutive underscores
# This excludes dashes '-', punct (',' or '.' etc).
# Valid: 'my_collection', 'stuff', 'the_0cho', 'abc123'
# Invalid: '_main', 'dots.inname', 'TheBigExampleCo',
#          'kilroy-_____-was_here', '¯\_(ツ)_/¯ ', '11__'
NAME_REGEXP = re.compile(r'^(?!.*__)[a-z]+[0-9a-z_]*$')

# Valid: 'abc123', 'blip'
# Invalid: '2legit2fast2sig11', '123abc', '10_9_8'
# see https://github.com/ansible/galaxy/issues/957
MATCH_LEADING_NUMBER_REGEXP = re.compile(r'^[0-9]')


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


@attr.s(frozen=True)
class CollectionInfo(object):
    namespace = attr.ib(default=None)
    name = attr.ib(default=None)
    version = attr.ib(default=None)
    # license = attr.ib(default=None)
    license = attr.ib(factory=list, converter=convert_single_to_list)
    description = attr.ib(default=None)

    repository = attr.ib(default=None)
    documentation = attr.ib(default=None)
    homepage = attr.ib(default=None)
    issues = attr.ib(default=None)

    authors = attr.ib(factory=list)
    tags = attr.ib(factory=list)

    # TODO: check these are valid paths at some point
    license_file = attr.ib(default=None,
                           validator=attr.validators.optional(attr.validators.instance_of(six.string_types)))
    readme = attr.ib(default=None,
                     validator=attr.validators.optional(attr.validators.instance_of(six.string_types)))

    # Note galaxy.yml 'dependencies' field is what mazer and ansible
    # consider 'requirements'. ie, install time requirements.
    dependencies = attr.ib(factory=dict, converter=convert_none_to_empty_dict)

    def __attrs_post_init__(self):
        # validate with have something in license or license_file
        self._check_for_license_or_license_file(self.license, self.license_file)

    @property
    def label(self):
        return '%s.%s' % (self.namespace, self.name)

    @staticmethod
    def value_error(msg):
        raise ValueError("Invalid collection metadata. %s" % msg)

    @namespace.validator
    @name.validator
    @version.validator
    def _check_required(self, attribute, value):
        if value is None:
            self.value_error("'%s' is required" % attribute.name)

    @version.validator
    def _check_version_format(self, attribute, value):
        if not semantic_version.validate(value):
            self.value_error("Expecting '%s' to be in semantic version format, "
                             "instead found '%s'." % (attribute.name, value))

    def _check_for_license_or_license_file(self, license_ids, license_file):
        if license_ids or license_file:
            return

        self.value_error("Valid values for 'license' or 'license_file' are required. "
                         "But 'license' (%s) and 'license_file' (%s) were invalid." % (license_ids, license_file))

    @license.validator
    def _check_licenses(self, attribute, value):
        '''Validate that 'licenses' value is a list of valid license identifiers'''

        # load or return already loaded data
        valid_license_ids = spdx_licenses.get_spdx()

        invalid_licenses = [license_id for license_id in value if not self._is_valid_license_id(license_id, valid_license_ids)]

        if invalid_licenses:
            self.value_error("Expecting '%s' to be a list of valid SPDX license identifiers, instead found invalid license identifiers: '%s' "
                             "in 'license' value %s. "
                             "For more info, visit https://spdx.org" % (attribute.name,
                                                                        ','.join([str(license_value) for license_value in invalid_licenses]),
                                                                        value))

    @staticmethod
    def _is_valid_license_id(license_id, valid_license_ids):
        if license_id is None:
            return False

        valid = valid_license_ids.get(license_id, None)
        if valid is None:
            return False

        # license was in list, but is deprecated
        if valid and valid.get('deprecated', None):
            print("Warning: collection metadata 'license' ID '%s' is "
                  "deprecated." % license_id)

        return True

    @authors.validator
    @tags.validator
    def _check_list_type(self, attribute, value):
        if not isinstance(value, list):
            self.value_error("Expecting '%s' to be a list" % attribute.name)

    @dependencies.validator
    def _check_dependencies_type(self, attribute, value):
        if not isinstance(value, dict) or value is None:
            self.value_error("Expecting '%s' to be a dict" % attribute.name)

    @tags.validator
    def _check_keywords(self, attribute, value):
        for k in value:
            if not re.match(TAG_REGEXP, k):
                self.value_error("Expecting %s to contain lowercase alphanumeric characters only, "
                                 "instead found '%s'." % (attribute.name, k))

    @name.validator
    @namespace.validator
    def _check_name(self, _unused, value):
        if '.' in value:
            self.value_error("Expecting 'name' and 'namespace' to not include any '.' but '%s' has a '.'" % value)
        if re.match(MATCH_LEADING_NUMBER_REGEXP, value):
            self.value_error("Expecting 'name' and 'namespace' to not start with a number but '%s' did" % value)
        # since the NAME_REGEXP catches use of hyphen '-' at all, the next check doesn't need to check for leading hyphen
        if value.startswith(('_',)):
            self.value_error("Expecting 'name' and 'namespace' to not start with '_' but '%s' did" % value)
        if not re.match(NAME_REGEXP, value):
            self.value_error("Expecting 'name' and 'namespace' to contain only lowercase alphanumeric characters or '_' only but '%s' contains others" % value)
