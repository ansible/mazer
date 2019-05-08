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
    # TODO: do some caching, invalidation based on dir mtimes?
    try:
        # TODO: filter on any rules for what a namespace path looks like
        #       may one being 'somenamespace.somename' (a dot sep ns and name)
        #
        repository_paths = os.listdir(namespace_path)
    except OSError as e:
        log.exception(e)
        log.warning('The namespace path %s did not exist so no repositories were found.',
                    namespace_path)
        repository_paths = []

    return repository_paths


def installed_repository_iterator(galaxy_context,
                                  namespace_match_filter=None,
                                  repository_spec_match_filter=None,
                                  requirement_spec_match_filter=None):
    '''For each repository in galaxy_context.collections_path, yield matching repositories'''

    namespace_match_filter = namespace_match_filter or matchers.MatchAll()
    repository_spec_match_filter = repository_spec_match_filter or matchers.MatchAll()
    requirement_spec_match_filter = requirement_spec_match_filter or matchers.MatchAll()

    installed_namespace_db = installed_namespaces_db.InstalledNamespaceDatabase(galaxy_context)

    # TODO: iterate/filter per namespace, then per collection
    for namespace in installed_namespace_db.select(namespace_match_filter=namespace_match_filter):
        log.debug('Looking for repos in namespace "%s"', namespace.namespace)

        # TODO: filter potential repository_paths based on repository_match_filer before we
        #       try to listdir() instead of after
        repository_paths = get_repository_paths(namespace.path)

        for repository_path in repository_paths:

            # TODO: just build up one dir and pass it in
            # TODO: if we need to distinquish repo from collection or role, we could do it here
            repository_ = repository.load_from_dir(galaxy_context.collections_path,
                                                   namespace_path=namespace.path,
                                                   namespace=namespace.namespace,
                                                   name=repository_path,
                                                   installed=True)

            # log.debug('candidate installed repo (pre filter): %s', repository_)

            if repository_spec_match_filter(repository_):
                log.debug('Found repository "%s" (%s) in namespace "%s"', repository_path, str(repository), namespace.namespace)

                if requirement_spec_match_filter(repository_):
                    log.debug('Found repository "%s" in namespace "%s"',
                              repository_path, namespace.namespace)
                    yield repository_


# TODO: add a get(namespace_id, repository_id) for loading a known ns.n directly without iterating
# TODO: add a contains(namespace_id, repository_id, matchers) for checking for existince
#       without loading the Repository from disk. Useful for things
#       like 'is some_repo_spec already installed?'
class InstalledRepositoryDatabase(object):

    def __init__(self, installed_context=None):
        self.installed_context = installed_context

    # TODO: add a repository_type_filter (ie, 'collection' or 'role' or 'other' etc)
    # TODO: something like namespace_condition or namespace_callable might be more accurate
    # TODO: "search" would be more accurate name for select()
    def select(self, namespace_match_filter=None,
               repository_spec_match_filter=None,
               requirement_spec_match_filter=None):
        # ie, default to select * more or less
        namespace_match_filter = namespace_match_filter or matchers.MatchAll()
        repository_spec_match_filter = repository_spec_match_filter or matchers.MatchAll()
        requirement_spec_match_filter = requirement_spec_match_filter or matchers.MatchAll()

        # log.debug('repository_spec_match_filter: %s', repository_spec_match_filter)

        installed_repositories = installed_repository_iterator(self.installed_context,
                                                               namespace_match_filter=namespace_match_filter,
                                                               repository_spec_match_filter=repository_spec_match_filter,
                                                               requirement_spec_match_filter=requirement_spec_match_filter)

        for matched_installed_repository in installed_repositories:
            yield matched_installed_repository

    def by_repository_spec(self, repository_spec):
        repository_spec_match_filter = matchers.MatchRepositorySpec([repository_spec])
        return self.select(repository_spec_match_filter=repository_spec_match_filter)

    def by_requirement(self, requirement):
        requirement_spec = requirement.requirement_spec

        return self.by_requirement_spec(requirement_spec=requirement_spec)

    def by_requirement_spec(self, requirement_spec):
        requirement_spec_match_filter = matchers.MatchRepositoryToRequirementSpec([requirement_spec])

        return self.select(requirement_spec_match_filter=requirement_spec_match_filter)
