import logging

from distutils.version import LooseVersion

from ansible_galaxy import exceptions

log = logging.getLogger(__name__)


def get_content_version(content_data, version, content_versions, content_content_name):
    '''find and compare content version found in content_data dict

    content_data is a dict based on /api/v1/content/13 for ex
    content_content_data is the name of the content specified by user?
    version is the currently set version?
    content_versions is ?
    '''
    log.debug('content_data: %s', content_data)
    log.debug('version: %s', version)
    log.debug('content_versions: %s', content_versions)
    log.debug('content_content_name: %s', content_content_name)

    if version and version != 'master':
        if content_versions and str(version) not in [a.get('name', None) for a in content_versions]:
            msg = "- the specified version (%s) of %s was not found in the list of available versions (%s)." % \
                (version, content_content_name, content_versions)
            raise exceptions.GalaxyError(msg)
    # and sort them to get the latest version. If there
    # are no versions in the list, we'll grab the head
    # of the master branch
    if len(content_versions) > 0:
        loose_versions = [LooseVersion(a.get('name', None)) for a in content_versions]
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
    return content_version
