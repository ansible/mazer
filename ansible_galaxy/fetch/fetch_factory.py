import logging

from ansible_galaxy import exceptions
from ansible_galaxy.fetch import galaxy_url
from ansible_galaxy.fetch import local_file
from ansible_galaxy.fetch import remote_url
from ansible_galaxy.fetch import scm_url
from ansible_galaxy.fetch import editable
from ansible_galaxy.models.repository_spec import FetchMethods

log = logging.getLogger(__name__)


def get(galaxy_context, requirement_spec):
    """determine how to download a repo, builds a fetch instance, and returns the instance"""

    fetcher = None

    # FIXME: note that ignore_certs for the galaxy
    # server(galaxy_context.server['ignore_certs'])
    # does not really imply that the repo archive download should ignore certs as well
    # (galaxy api server vs cdn) but for now, we use the value for both

    if requirement_spec.fetch_method == FetchMethods.EDITABLE:
        fetcher = editable.EditableFetch(requirement_spec=requirement_spec,
                                         galaxy_context=galaxy_context)
    elif requirement_spec.fetch_method == FetchMethods.SCM_URL:
        fetcher = scm_url.ScmUrlFetch(requirement_spec=requirement_spec)
    elif requirement_spec.fetch_method == FetchMethods.LOCAL_FILE:
        # the file is a tar, so open it that way and extract it
        # to the specified (or default) content directory
        fetcher = local_file.LocalFileFetch(requirement_spec)
    elif requirement_spec.fetch_method == FetchMethods.REMOTE_URL:
        fetcher = remote_url.RemoteUrlFetch(requirement_spec=requirement_spec,
                                            validate_certs=not galaxy_context.server['ignore_certs'])
    elif requirement_spec.fetch_method == FetchMethods.GALAXY_URL:
        fetcher = galaxy_url.GalaxyUrlFetch(requirement_spec=requirement_spec,
                                            galaxy_context=galaxy_context)
    else:
        raise exceptions.GalaxyError('No approriate content fetcher found for %s %s',
                                     requirement_spec.scm, requirement_spec.src)

    log.debug('Using fetcher: %s for requirement_spec: %r', fetcher, requirement_spec)

    return fetcher
