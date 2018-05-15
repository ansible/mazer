import json
import logging

from distutils.version import LooseVersion

from ansible_galaxy import exceptions
from ansible_galaxy.utils.version import normalize_version_string

log = logging.getLogger(__name__)


def get_content_version(content_data, version, content_versions, content_content_name):
    '''find and compare content version found in content_data dict

    content_data is a dict based on /api/v1/content/13 for ex
    content_content_data is the name of the content specified by user?
    version is the currently set version?
    content_versions is a list of version strings in order
    '''

    log.debug('%s want ver: %s', content_content_name, version)
    log.debug('%s vers avail: %s',
              content_content_name, json.dumps(content_versions, indent=2))

    normalized_versions = [normalize_version_string(x) for x in content_versions]
    if version and version != 'master':
        if not normalized_versions:
            msg = "- The list of available versions for %s is empty (%s)." % \
                (content_content_name or 'content', normalized_versions)
            raise exceptions.GalaxyError(msg)

        if str(version) not in normalized_versions:
            msg = "- the specified version (%s) of %s was not found in the list of available versions (%s)." % \
                (version, content_content_name or 'content', normalized_versions)
            raise exceptions.GalaxyError(msg)

        # if we get here, 'version' is in normalized_versions
        # return the exact match version since it was available
        log.debug('%s using requested ver: %s', content_content_name, version)
        return version

    # and sort them to get the latest version. If there
    # are no versions in the list, we'll grab the head
    # of the master branch
    if len(normalized_versions) > 0:
        loose_versions = [LooseVersion(a) for a in normalized_versions]
        try:
            loose_versions.sort()
        except TypeError:
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
