import logging
import os

from ansible_galaxy import matchers
from ansible_galaxy import installed_namespaces_db
from ansible_galaxy.models.content_repository import ContentRepository
from ansible_galaxy.models.content_spec import ContentSpec

log = logging.getLogger(__name__)


def repository_match_all(content_repository):
    return True


def get_repository_paths(namespace_path):
    # TODO: abstract this a bit?  one to make it easier to mock, but also
    #       possibly to prepare for nested dirs, multiple paths, various
    #       filters/whitelist/blacklist/excludes, caching, or respecting
    #       fs ordering, etc
    try:
        # TODO: filter on any rules for what a namespace path looks like
        #       may one being 'somenamespace.somename' (a dot sep ns and name)
        #
        repository_paths = os.listdir(namespace_path)
    except OSError as e:
        log.exception(e)
        log.warn('The namespace path %s did not exist so no content or repositories were found.',
                 namespace_path)
        repository_paths = []

    return repository_paths


def installed_repository_iterator(galaxy_context,
                                  namespace_match_filter=None,
                                  repository_match_filter=None):

    namespace_match_filter = namespace_match_filter or matchers.MatchAll()
    repository_match_filter = repository_match_filter or matchers.MatchAll()

    content_path = galaxy_context.content_path

    installed_namespace_db = installed_namespaces_db.InstalledNamespaceDatabase(galaxy_context)

    # repository_paths = get_repository_paths(content_path)

    # log.debug('repository_paths for content_path=%s: %s', content_path, repository_paths)

    for namespace in installed_namespace_db.select(namespace_match_filter=namespace_match_filter):
        # log.debug('namespace: %s', namespace)
        log.debug('Looking for repos in namespace "%s"', namespace.namespace)

        repository_paths = get_repository_paths(namespace.path)

        for repository_path in repository_paths:
            # use the default 'local' style content_spec_parse and name resolver
            # spec_data = content_spec_parse.spec_data_from_string(repository_path)

            repository_full_path = os.path.join(content_path, namespace.namespace, repository_path)
            # log.debug('repo_fll_path: %s', repository_full_path)
            content_spec = ContentSpec(namespace=namespace.namespace,
                                       name=repository_path)
            content_repository = ContentRepository(content_spec=content_spec,
                                                   path=repository_full_path)

            # log.debug('content_repo: %s', content_repository)
            # log.debug('match: %s(%s) %s', repository_match_filter, content_repository, repository_match_filter(content_repository))
            if repository_match_filter(content_repository):
                log.debug('Found repo "%s" in namespace "%s"', repository_path, namespace.namespace)
                yield content_repository


class InstalledRepositoryDatabase(object):

    def __init__(self, installed_context=None):
        self.installed_context = installed_context

    def select(self, namespace_match_filter=None, repository_match_filter=None):
        # ie, default to select * more or less
        repository_match_filter = repository_match_filter or matchers.MatchAll()
        namespace_match_filter = namespace_match_filter or matchers.MatchAll()

        installed_repositories = installed_repository_iterator(self.installed_context,
                                                               namespace_match_filter=namespace_match_filter,
                                                               repository_match_filter=repository_match_filter)

        for matched_repository in installed_repositories:
            yield matched_repository
