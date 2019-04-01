import logging

import semantic_version

from ansible_galaxy import exceptions
from ansible_galaxy.utils.version import normalize_version_string

log = logging.getLogger(__name__)


def sort_versions(versions):
    # list of tuples of loose_version and original string, the sort
    # will sort based on first value of tuple, then we return just the
    # original strings
    semver_versions = [(semantic_version.Version(a), a) for a in versions]
    semver_versions.sort()
    return [v[1] for v in semver_versions]


def normalize_versions(content_versions):
    # a list of tuples of (normalized_version, original_version) for building
    # map of normalized version to original version
    normalized_versions = [(normalize_version_string(x), x) for x in content_versions]
    available_normalized_versions = [v[0] for v in normalized_versions]

    # map the 'normalized' version back to the original version string, we need it for
    # content archive download urls
    # norm_to_orig_map = dict(normalized_versions)
    norm_to_orig_map = normalized_versions

    return (available_normalized_versions, norm_to_orig_map)


def validate_versions(content_versions):
    valid_versions = []
    invalid_versions = []
    for version in content_versions:
        if not semantic_version.validate(version):
            log.warning('The version string "%s" is not valid, skipping.', version)
            invalid_versions.append(version)
            continue
        valid_versions.append(version)

    return (valid_versions, invalid_versions)


def get_repository_version(repository_data, requirement_spec, repository_versions):
    '''find and compare repository version found in repository_data dict

    repository_data is a dict based on /api/v1/repositories/13 for ex
    content_content_data is the name of the content specified by user?
    version is the version string asked for by user
    content_versions is a list of version strings in order
    '''

    log.debug('%s wants ver: %s type: %s', requirement_spec.name, requirement_spec.version_spec, type(requirement_spec.version_spec))

    # normalize versions, but also build a map of the normalized version string to the orig string
    available_normalized_versions, norm_to_orig_map = normalize_versions(repository_versions)

    # verify that the normalized versions are valid semver now so that we dont worry about it
    # in the sort
    available_versions, dummy = \
        validate_versions(available_normalized_versions)

    # we specified a particular version is required so look for it in available versions
    if not available_versions:
        # FIXME: should we show the actual available versions or the available
        #        versions we searched in?  act: ['v1.0.0', '1.1'] nor: ['1.0.0', '1.1']
        msg = "- The list of available versions for %s is empty (%s)." % \
            (requirement_spec.label or 'content', available_versions)
        raise exceptions.GalaxyError(msg)

    semver_available_versions = [semantic_version.Version(ver) for ver in available_versions]

    latest_version = requirement_spec.version_spec.select(semver_available_versions)
    if latest_version is None:
        # TODO: how do we msg 'couldn't find the version you specified
        #       in actual version tags or ones we made up without the leading v'
        msg = "- the specified version spec (%s) of %s was not found in the list of available versions (%s)." % \
            (requirement_spec.version_spec, requirement_spec.label or 'content', available_versions)
        raise exceptions.GalaxyError(msg)

    # if we get here, 'version' is in available_normalized_versions
    # return the exact match version since it was available
    latest_version_str = str(latest_version)

    # have to use list of tuples here since we can have multiple identical keys with different values
    norm_to_orig = [x for x in norm_to_orig_map if x[0] == latest_version_str]

    if len(norm_to_orig) > 1:
        unnormal_versions = [ver_alias[1] for ver_alias in norm_to_orig]
        raise exceptions.GalaxyClientError('There are ambiguous and contradicting version numbers (%s) that match version spec "%s"' %
                                           (', '.join(unnormal_versions), str(requirement_spec.version_spec)))

    orig_version_str = norm_to_orig[0][1]

    log.debug('%s requested ver: %s, matched: %s, using real ver: %s ', requirement_spec.label, requirement_spec.version_spec, latest_version, orig_version_str)

    return orig_version_str
