import glob
import logging
import os

from ansible_galaxy import installed_repository_db
from ansible_galaxy import matchers
from ansible_galaxy.flat_rest_api.content import InstalledContent

log = logging.getLogger(__name__)


# need a content_type matcher?
def installed_repository_role_iterator(repository_path):

    repository_roles_dirs = glob.glob('%s/%s/*' % (repository_path, 'roles'))
    for repository_roles_path in repository_roles_dirs:
        # full_content_paths.append(namespaced_roles_path)
        # log.debug('rrp: %s', repository_roles_path)
        yield repository_roles_path


installed_repository_content_iterator_map = {'roles': installed_repository_role_iterator}


def installed_content_iterator(galaxy_context,
                               namespace_match_filter=None,
                               repository_match_filter=None,
                               content_match_filter=None,
                               content_type=None):

    # match_all works for all types
    namespace_match_filter = namespace_match_filter or matchers.MatchAll()
    repository_match_filter = repository_match_filter or matchers.MatchAll()
    content_match_filter = content_match_filter or matchers.MatchAll()

    content_type = content_type or 'roles'

    installed_repo_db = installed_repository_db.InstalledRepositoryDatabase(galaxy_context)

    # for namespace_full_path in namespace_paths_iterator:
    for installed_repository in installed_repo_db.select(namespace_match_filter=namespace_match_filter,
                                                         repository_match_filter=repository_match_filter):
        log.debug('Found repo "%s" at %s', installed_repository.content_spec.label, installed_repository.path)
        installed_repository_full_path = installed_repository.path

        if not repository_match_filter(installed_repository):
            log.debug('The repo_match_filter %s failed to match for %s', repository_match_filter, installed_repository)
            continue

        # since we will need a different iterator for each specific type of content, consult
        # a map of content_type->iterator_method however there is only a 'roles' iterator for now
        installed_repository_content_iterator_method = \
            installed_repository_content_iterator_map.get(content_type)

        if installed_repository_content_iterator_method is None:
            continue

        installed_repository_content_iterator = installed_repository_content_iterator_method(installed_repository_full_path)

        log.debug('Looking for %s in repo at %s', content_type, installed_repository_full_path)
        for installed_content_full_path in installed_repository_content_iterator:

            repo_namespace = installed_repository.content_spec.namespace
            path_file = os.path.basename(installed_content_full_path)

            gr = InstalledContent(galaxy_context, path_file, namespace=repo_namespace, path=installed_content_full_path)

            log.debug('Found %s "%s" at %s', gr.content_type, gr.name, installed_content_full_path)

            log.debug('gr.metadata: %s', gr.metadata)

            version = None

            # TODO: should probably sep the generator for getting the InstalledContent objects from the generator that
            #       creates the content_info returns instead of intertwining them
            if gr.metadata or gr.install_info:
                version = gr.install_info.version or "(unknown version)"

            if not content_match_filter(gr):
                log.debug('%s was not matched by content_match_filter: %s', gr, content_match_filter)
                continue

            # this is sort of the 'join' of installed_repository and installed_content
            content_info = {'path': path_file,
                            'content_data': gr,
                            'installed_repository': installed_repository,
                            'version': version,
                            }

            yield content_info


class InstalledContentDatabase(object):

    def __init__(self, installed_context=None):
        self.installed_context = installed_context

    # select content based on matching the installed namespace.repository and/or the content itself
    def select(self, repository_match_filter=None, content_match_filter=None):
        # ie, default to select * more or less
        repository_match_filter = repository_match_filter or matchers.MatchAll()
        content_match_filter = content_match_filter or matchers.MatchAll()

        roles_content_iterator = installed_content_iterator(self.installed_context,
                                                            content_type='roles',
                                                            repository_match_filter=repository_match_filter,
                                                            content_match_filter=content_match_filter)

        for matched_content in roles_content_iterator:
            yield matched_content
