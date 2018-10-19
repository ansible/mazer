import logging
import os

from ansible_galaxy import repository
from ansible_galaxy import matchers
from ansible_galaxy import installed_namespaces_db

log = logging.getLogger(__name__)


def get_repository_paths(namespace_path):
    # TODO: abstract this a bit?  one to make it easier to mock, but also
    #       possibly to prepare for nested dirs, multiple paths, various
    #       filters/whitelist/blacklist/excludes, caching, or respecting
    #       fs ordering, etc
    #
    try:
        # TODO: filter on any rules for what a namespace path looks like
        #       may one being 'somenamespace.somename' (a dot sep ns and name)
        #
        repository_paths = os.listdir(namespace_path)
    except OSError as e:
        log.exception(e)
        log.warn('The namespace path %s did not exist so no repositories were found.',
                 namespace_path)
        repository_paths = []

    return repository_paths


def installed_repository_iterator(galaxy_context,
                                  namespace_match_filter=None,
                                  repository_match_filter=None):
    '''For each repository in galaxy_context.content_path, yield matching repositories'''

    namespace_match_filter = namespace_match_filter or matchers.MatchAll()
    repository_match_filter = repository_match_filter or matchers.MatchAll()

    installed_namespace_db = installed_namespaces_db.InstalledNamespaceDatabase(galaxy_context)

    # TODO: iterate/filter per namespace, then per repository, then per collection/role/etc
    for namespace in installed_namespace_db.select(namespace_match_filter=namespace_match_filter):
        log.debug('Looking for repos in namespace "%s"', namespace.namespace)

        repository_paths = get_repository_paths(namespace.path)

        for repository_path in repository_paths:

            # TODO: if we need to distinquish repo from collection or role, we could do it here
            repository_ = repository.load_from_dir(galaxy_context.content_path,
                                                   namespace=namespace.namespace,
                                                   name=repository_path,
                                                   installed=True)

            log.debug('candidate installed repo (pre filter): %s', repository_)

            if repository_match_filter(repository_):
                log.debug('Found repository "%s" in namespace "%s"', repository_path, namespace.namespace)
                yield repository_


class InstalledRepositoryDatabase(object):

    def __init__(self, installed_context=None):
        self.installed_context = installed_context

    # TODO: add a repository_type_filter (ie, 'collection' or 'role' or 'other' etc)
    def select(self, namespace_match_filter=None, repository_match_filter=None):
        # ie, default to select * more or less
        repository_match_filter = repository_match_filter or matchers.MatchAll()
        namespace_match_filter = namespace_match_filter or matchers.MatchAll()

        installed_repositories = installed_repository_iterator(self.installed_context,
                                                               namespace_match_filter=namespace_match_filter,
                                                               repository_match_filter=repository_match_filter)

        for matched_installed_repository in installed_repositories:
            yield matched_installed_repository
