import logging

from ansible_galaxy import exceptions
from ansible_galaxy.content_spec import FetchMethods
from ansible_galaxy.fetch import galaxy_url
from ansible_galaxy.fetch import local_file
from ansible_galaxy.fetch import remote_url
from ansible_galaxy.fetch import scm_url

log = logging.getLogger()


def get(galaxy_context, content_spec):
    """determine how to download a repo, builds a fetch instance, and returns the instance"""

    fetcher = None
    # FIXME: note that ignore_certs for the galaxy
    # server(galaxy_context.server['ignore_certs'])
    # does not really imply that the repo archive download should ignore certs as well
    # (galaxy api server vs cdn) but for now, we use the value for both
    if content_spec.fetch_method == FetchMethods.SCM_URL:
        fetcher = scm_url.ScmUrlFetch(content_spec=content_spec)
    elif content_spec.fetch_method == FetchMethods.LOCAL_FILE:
        # the file is a tar, so open it that way and extract it
        # to the specified (or default) content directory
        fetcher = local_file.LocalFileFetch(content_spec)
    elif content_spec.fetch_method == FetchMethods.REMOTE_URL:
        fetcher = remote_url.RemoteUrlFetch(content_spec=content_spec,
                                            validate_certs=not galaxy_context.server['ignore_certs'])
    elif content_spec.fetch_method == FetchMethods.GALAXY_URL:
        fetcher = galaxy_url.GalaxyUrlFetch(content_spec=content_spec.src,
                                            content_version=content_spec.version,
                                            galaxy_context=galaxy_context)
    else:
        raise exceptions.GalaxyError('No approriate content fetcher found for %s %s',
                                     content_spec.scm, content_spec.src)
    return fetcher
