from __future__ import print_function

import attr
import json
import logging
import os
import re
import semver

log = logging.getLogger(__name__)

TAG_REGEXP = re.compile('^[a-z0-9]+$')
NAME_REGEXP = re.compile(r'^[a-z0-9_-]+$')
# see https://github.com/ansible/galaxy/issues/957


@attr.s(frozen=True)
class CollectionInfo(object):
    namespace = attr.ib(default=None)
    name = attr.ib(default=None)
    version = attr.ib(default=None)
    license = attr.ib(default=None)
    description = attr.ib(default=None)

    authors = attr.ib(factory=list)
    keywords = attr.ib(factory=list)
    readme = attr.ib(default='README.md')

    # Note galaxy.yml 'dependencies' field is what mazer and ansible
    # consider 'requirements'. ie, install time requirements.
    dependencies = attr.ib(factory=list)

    @property
    def label(self):
        return '%s.%s' % (self.namespace, self.name)

    @staticmethod
    def value_error(msg):
        raise ValueError("Invalid collection metadata. %s" % msg)

    @namespace.validator
    @name.validator
    @version.validator
    @license.validator
    @description.validator
    def _check_required(self, attribute, value):
        if value is None:
            self.value_error("'%s' is required" % attribute.name)

    @version.validator
    def _check_version_format(self, attribute, value):
        try:
            semver.parse_version_info(value)
        except ValueError:
            self.value_error("Expecting 'version' to be in semantic version format, "
                             "instead found '%s'." % value)

    @license.validator
    def _check_license(self, attribute, value):
        cwd = os.path.dirname(os.path.abspath(__file__))
        license_path = os.path.join(cwd, '..', 'data', 'spdx_licenses.json')
        license_data = json.load(open(license_path, 'r'))
        for lic in license_data['licenses']:
            if lic['licenseId'] == value:
                if lic['isDeprecatedLicenseId']:
                    print("Warning: collection metadata 'license' value '%s' is "
                          "deprecated." % value)
                return True
        self.value_error("Expecting 'license' to be a valid SPDX license ID, instead found '%s'. "
                         "For more info, visit https://spdx.org" % value)

    @authors.validator
    @keywords.validator
    @dependencies.validator
    def _check_list_type(self, attribute, value):
        if not isinstance(value, list):
            self.value_error("Expecting '%s' to be a list" % attribute.name)

    @keywords.validator
    def _check_keywords(self, attribute, value):
        for k in value:
            if not re.match(TAG_REGEXP, k):
                self.value_error("Expecting keywords to contain alphanumeric characters only, "
                                 "instead found '%s'." % k)

    @name.validator
    @namespace.validator
    def _check_name(self, attribute, value):
        if '.' in value:
            self.value_error("Expecting 'name' and 'namespace' to not include any '.' but '%s' has a '.'" % value)
        if not re.match(NAME_REGEXP, value):
            self.value_error("Expecting 'name' and 'namespace' to contain alphanumeric characters, '-', or '_' only but '%s' contains others" % value)
        if value.startswith(('-', '_')):
            self.value_error("Expecting 'name' and 'namespace' to not start with '-' or '_' but '%s' did" % value)
