import logging
import os

from ansible_galaxy import content_spec_parse
from ansible_galaxy import matchers
from ansible_galaxy.models.content_repository import ContentRepository

log = logging.getLogger(__name__)


def repository_match_all(content_repository):
    return True


def get_repository_paths(content_path):
    # TODO: abstract this a bit?  one to make it easier to mock, but also
    #       possibly to prepare for nested dirs, multiple paths, various
    #       filters/whitelist/blacklist/excludes, caching, or respecting
    #       fs ordering, etc
    try:
        # TODO: filter on any rules for what a namespace path looks like
        #       may one being 'somenamespace.somename' (a dot sep ns and name)
        #
        namespace_paths = os.listdir(content_path)
    except OSError as e:
        log.exception(e)
        log.warn('The content path %s did not exist so no content or repositories were found.',
                 content_path)
        namespace_paths = []

    return namespace_paths


def installed_repository_iterator(galaxy_context,
                                  match_filter=None):

    repository_match_filter = match_filter or matchers.MatchAll()
    content_path = galaxy_context.content_path

    repository_paths = get_repository_paths(content_path)

    log.debug('repository_paths for content_path=%s: %s', content_path, repository_paths)

    for repository_path in repository_paths:
        # log.debug('repo_path: %s', repository_path)
        # use the default 'local' style content_spec_parse and name resolver
        spec_data = content_spec_parse.spec_data_from_string(repository_path)

        repository_full_path = os.path.join(content_path, repository_path)
        # log.debug('repo_fll_path: %s', repository_full_path)
        content_repository = ContentRepository(namespace=spec_data.get('namespace'),
                                               name=spec_data.get('name'),
                                               path=repository_full_path)

        # log.debug('content_repo: %s', content_repository)
        # log.debug('match: %s(%s) %s', repository_match_filter, content_repository, repository_match_filter(content_repository))
        if repository_match_filter(content_repository):
            yield content_repository


class InstalledRepositoryDatabase(object):

    def __init__(self, installed_context=None):
        self.installed_context = installed_context

    def select(self, repository_match_filter=None):
        # ie, default to select * more or less
        repository_match_filter = repository_match_filter or repository_match_all

        installed_repositories = installed_repository_iterator(self.installed_context,
                                                               match_filter=repository_match_filter)

        for matched_repository in installed_repositories:
            yield matched_repository
