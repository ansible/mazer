import logging
import re

import semantic_version

log = logging.getLogger(__name__)

VERSION_WITH_LEADING_V_MATCH_RE = re.compile(r'^[vV]\d+\.')
VERSION_WITH_LEADING_V_SUB_RE = re.compile(r'(^[vV])')


def convert_string_to_semver(version):
    # log.debug('vs: %s type: %s', version, type(version))

    if version is None:
        return None

    if isinstance(version, semantic_version.Version):
        return version

    return semantic_version.Version(version)


def convert_string_to_version_spec(version_spec):
    # TODO: or the default '*' spec?
    if version_spec is None:
        return None

    if isinstance(version_spec, semantic_version.Spec):
        return version_spec

    return semantic_version.Spec(version_spec)


def version_needs_aka(version_string):
    '''Return True if version_string is in v1.0.0 form'''
    if not version_string:
        return False

    matches = VERSION_WITH_LEADING_V_MATCH_RE.match(version_string)

    if not matches:
        return False

    return True


def normalize_version_string(version_string):
    '''Normalize any version strings (rm 'v' from 'v1.0.0' for ex


    https://github.com/ansible/galaxy-cli/wiki/Content-Versioning#versions-in-galaxy-cli

    "When providing a version, provide the semantic version with or without the leading 'v' or 'V'."

    strip off leading v or V, and return a version string without it.'''

    if not version_string:
        return version_string

    matches = VERSION_WITH_LEADING_V_MATCH_RE.match(version_string)

    if not matches:
        return version_string

    new_versions_string = VERSION_WITH_LEADING_V_SUB_RE.sub('', version_string, 1)

    log.warning('Stripping leading "v" or "V" from version string "%s", new version string is  "%s"',
                version_string, new_versions_string)

    return new_versions_string
