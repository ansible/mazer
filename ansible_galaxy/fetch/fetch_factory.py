import logging

from ansible_galaxy import exceptions
from ansible_galaxy.repository_spec import FetchMethods
from ansible_galaxy.fetch import galaxy_url
from ansible_galaxy.fetch import local_file
from ansible_galaxy.fetch import remote_url
from ansible_galaxy.fetch import scm_url
from ansible_galaxy.fetch import editable

log = logging.getLogger(__name__)


def get(galaxy_context, repository_spec):
    """determine how to download a repo, builds a fetch instance, and returns the instance"""

    fetcher = None

    # FIXME: note that ignore_certs for the galaxy
    # server(galaxy_context.server['ignore_certs'])
    # does not really imply that the repo archive download should ignore certs as well
    # (galaxy api server vs cdn) but for now, we use the value for both

    log.debug('repository_spec: %r', repository_spec)
    log.debug('repository_spec.fetch_method %s dir(fetchMethods): %s',
              repository_spec.fetch_method, dir(FetchMethods))

    if repository_spec.fetch_method == FetchMethods.EDITABLE:
        fetcher = editable.EditableFetch(repository_spec=repository_spec,
                                         galaxy_context=galaxy_context)
    elif repository_spec.fetch_method == FetchMethods.SCM_URL:
        fetcher = scm_url.ScmUrlFetch(repository_spec=repository_spec)
    elif repository_spec.fetch_method == FetchMethods.LOCAL_FILE:
        # the file is a tar, so open it that way and extract it
        # to the specified (or default) content directory
        fetcher = local_file.LocalFileFetch(repository_spec)
    elif repository_spec.fetch_method == FetchMethods.REMOTE_URL:
        fetcher = remote_url.RemoteUrlFetch(repository_spec=repository_spec,
                                            validate_certs=not galaxy_context.server['ignore_certs'])
    elif repository_spec.fetch_method == FetchMethods.GALAXY_URL:
        fetcher = galaxy_url.GalaxyUrlFetch(repository_spec=repository_spec,
                                            galaxy_context=galaxy_context)
    else:
        raise exceptions.GalaxyError('No approriate content fetcher found for %s %s',
                                     repository_spec.scm, repository_spec.src)
    return fetcher
