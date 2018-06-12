import logging

from distutils.version import LooseVersion

from ansible_galaxy import exceptions
from ansible_galaxy.utils.version import normalize_version_string

log = logging.getLogger(__name__)


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

    # a list of tuples of (normalized_version, original_version) for building map of normalized version to original version
    normalized_versions = [(normalize_version_string(x), x) for x in content_versions]

    available_normalized_versions = [v[0] for v in normalized_versions]

    # map the 'normalized' version back to the original version string, we need it for content archive download urls
    norm_to_orig_map = dict(normalized_versions)

    normalized_version = normalize_version_string(version)

#    log.debug('normalized_version: %s', normalized_version)
#    log.debug('avail_normalized_versions: %s', json.dumps(available_normalized_versions, indent=4))

    # we specified a particular version is required so look for it in available versions
    if version and version != 'master':
        if not available_normalized_versions:
            # FIXME: should we show the actual available versions or the available
            #        versions we searched in?  act: ['v1.0.0', '1.1'] nor: ['1.0.0', '1.1']
            msg = "- The list of available versions for %s is empty (%s)." % \
                (content_content_name or 'content', available_normalized_versions)
            raise exceptions.GalaxyError(msg)

        if str(normalized_version) not in available_normalized_versions:
            # TODO: how do we msg 'couldn't find the version you specified
            #       in actual version tags or ones we made up without the leading v'
            msg = "- the specified version (%s) of %s was not found in the list of available versions (%s)." % \
                (version, content_content_name or 'content', available_normalized_versions)
            raise exceptions.GalaxyError(msg)

        # if we get here, 'version' is in available_normalized_versions
        # return the exact match version since it was available
        orig_version = norm_to_orig_map[normalized_version]
        log.debug('%s requested ver: %s, matched: %s, using real ver: %s ', content_content_name, version, normalized_version, orig_version)
        return orig_version

    # and sort them to get the latest version. If there
    # are no versions in the list, we'll grab the head
    # of the master branch
    if len(available_normalized_versions) > 0:
        loose_versions = [LooseVersion(a) for a in available_normalized_versions]
        try:
            loose_versions.sort()
        except TypeError as e:
            log.exception(e)
            log.error('ver: %s loose_versions: %s', version, loose_versions)
            raise exceptions.GalaxyClientError(
                'Unable to compare content versions (%s) to determine the most recent version due to incompatible version formats. '
                'Please contact the content author to resolve versioning conflicts, or specify an explicit content version to '
                'install.' % ', '.join([v.vstring for v in loose_versions])
            )
        content_version = str(loose_versions[-1])
    # FIXME: follow 'repository' branch and it's ['import_branch'] ?
    elif content_data.get('github_branch', None):
        content_version = content_data['github_branch']
    else:
        content_version = 'master'

    log.debug('%s using latest ver: %s', content_content_name, content_version)
    return content_version
