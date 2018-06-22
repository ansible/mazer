import logging

import semver

from ansible_galaxy import exceptions
from ansible_galaxy.utils.version import normalize_version_string

log = logging.getLogger(__name__)


def sort_versions(versions):
    # list of tuples of loose_version and original string, the sort
    # will sort based on first value of tuple, then we return just the
    # original strings
    semver_versions = [(semver.parse_version_info(a), a) for a in versions]
    semver_versions.sort()
    return [v[1] for v in semver_versions]


# TODO: somewhere we need to have a code path for the ordered version list returned from server
#       and another for the versions we got elsewhere.
def get_latest_version(available_normalized_versions, content_data):
    # and sort them to get the latest version. If there
    # are no versions in the list, we'll grab the head
    # of the master branch
    if available_normalized_versions:
        try:
            sorted_versions = sort_versions(available_normalized_versions)
        except (TypeError, ValueError) as e:
            log.exception(e)
            raise exceptions.GalaxyClientError(
                'Unable to compare content versions (%s) to determine the most recent version due to incompatible version formats. '
                'Please contact the content author to resolve versioning conflicts, or specify an explicit content version to install. '
                'The version error was: "%s"' % (', '.join(available_normalized_versions), e)
            )

        content_version = sorted_versions[-1]
    # FIXME: follow 'repository' branch and it's ['import_branch'] ?
    elif content_data.get('github_branch', None):
        content_version = content_data['github_branch']
    else:
        content_version = 'master'

    return content_version


def normalize_versions(content_versions):
    # a list of tuples of (normalized_version, original_version) for building
    # map of normalized version to original version
    normalized_versions = [(normalize_version_string(x), x) for x in content_versions]

    available_normalized_versions = [v[0] for v in normalized_versions]

    # map the 'normalized' version back to the original version string, we need it for
    # content archive download urls
    norm_to_orig_map = dict(normalized_versions)

    return (available_normalized_versions, norm_to_orig_map)


def validate_versions(content_versions):
    valid_versions = []
    invalid_versions = []
    for version in content_versions:
        try:
            semver.parse(version)
            valid_versions.append(version)
        except ValueError as e:
            log.exception(e)
            log.warning('The version string "%s" is not valid, skipping: %s', version, e)
            invalid_versions.append(version)
            continue

    return (valid_versions, invalid_versions)


# FIXME: rename, really get_repo_version
def get_content_version(content_data, version, content_versions, content_content_name):
    '''find and compare content version found in content_data dict

    content_data is a dict based on /api/v1/content/13 for ex
    content_content_data is the name of the content specified by user?
    version is the version string asked for by user
    content_versions is a list of version strings in order
    '''

    log.debug('%s want ver: %s', content_content_name, version)
#    log.debug('%s vers avail: %s',
#              content_content_name, json.dumps(content_versions, indent=2))

    # normalize versions, but also build a map of the normalized version string to the orig string
    available_normalized_versions, norm_to_orig_map = normalize_versions(content_versions)

    # verify that the normalized versions are valid semver now so that we dont worry about it
    # in the sort
    available_versions, dummy = \
        validate_versions(available_normalized_versions)

    normalized_version = normalize_version_string(version)

#    log.debug('normalized_version: %s', normalized_version)
#    log.debug('avail_normalized_versions: %s', json.dumps(available_normalized_versions, indent=4))

    # we specified a particular version is required so look for it in available versions
    if version and version != 'master':
        if not available_versions:
            # FIXME: should we show the actual available versions or the available
            #        versions we searched in?  act: ['v1.0.0', '1.1'] nor: ['1.0.0', '1.1']
            msg = "- The list of available versions for %s is empty (%s)." % \
                (content_content_name or 'content', available_versions)
            raise exceptions.GalaxyError(msg)

        if str(normalized_version) not in available_versions:
            # TODO: how do we msg 'couldn't find the version you specified
            #       in actual version tags or ones we made up without the leading v'
            msg = "- the specified version (%s) of %s was not found in the list of available versions (%s)." % \
                (version, content_content_name or 'content', available_versions)
            raise exceptions.GalaxyError(msg)

        # if we get here, 'version' is in available_normalized_versions
        # return the exact match version since it was available
        orig_version = norm_to_orig_map[normalized_version]
        log.debug('%s requested ver: %s, matched: %s, using real ver: %s ', content_content_name, version, normalized_version, orig_version)
        return orig_version

    # At this point, we have a list of the available versions. The available versions have
    # been normalized (leading 'v' or 'V' stripped off).
    # No specific version was requested, so we return the latest one.
    content_version = get_latest_version(available_versions, content_data)

    log.debug('%s using latest ver: %s', content_content_name, content_version)
    return content_version
