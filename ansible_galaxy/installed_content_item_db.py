import glob
import itertools
import logging
import os

from ansible_galaxy import installed_repository_db
from ansible_galaxy import matchers
from ansible_galaxy.models.content_item import ContentItem

log = logging.getLogger(__name__)


def role_content_path_iterator(repository):
    return glob.iglob('%s/%s/*' % (repository.path, 'roles'))


def module_content_path_iterator(repository):
    return glob.iglob('%s/%s/*' % (repository.path, 'modules'))


# need a content_type matcher?
def repository_content_iterator(repository, content_item_type, content_item_path_iterator_method):
    content_item_paths = content_item_path_iterator_method(repository)

    for content_item_path in content_item_paths:
        repo_namespace = repository.repository_spec.namespace
        path_file = os.path.basename(content_item_path)

        content_item = ContentItem(namespace=repo_namespace,
                                   name=path_file,
                                   path=path_file,
                                   content_item_type=content_item_type,
                                   version=repository.repository_spec.version)

        log.debug('Found %s "%s" at %s', content_item, content_item.name, path_file)
        yield content_item


def installed_content_item_iterator(galaxy_context,
                                    namespace_match_filter=None,
                                    repository_match_filter=None,
                                    content_item_match_filter=None,
                                    content_item_type=None):

    # match_all works for all types
    namespace_match_filter = namespace_match_filter or matchers.MatchAll()
    repository_match_filter = repository_match_filter or matchers.MatchAll()
    content_item_match_filter = content_item_match_filter or matchers.MatchAll()

    content_item_type = content_item_type or 'roles'

    installed_repo_db = installed_repository_db.InstalledRepositoryDatabase(galaxy_context)

    # for namespace_full_path in namespace_paths_iterator:
    for installed_repository in installed_repo_db.select(namespace_match_filter=namespace_match_filter,
                                                         repository_match_filter=repository_match_filter):
        log.debug('Found repository "%s" at %s', installed_repository.repository_spec.label, installed_repository.path)
        installed_repository_full_path = installed_repository.path

        if not repository_match_filter(installed_repository):
            log.debug('The repository_match_filter %s failed to match for %s', repository_match_filter, installed_repository)
            continue

        all_content_iterator = itertools.chain(repository_content_iterator(installed_repository,
                                                                           'roles',
                                                                           role_content_path_iterator),
                                               repository_content_iterator(installed_repository,
                                                                           'modules',
                                                                           module_content_path_iterator))

        log.debug('Looking for %s in repository at %s', content_item_type, installed_repository_full_path)
        for installed_content_item in all_content_iterator:
            log.debug('installed_content_item: %s', installed_content_item)

            if not content_item_match_filter(installed_content_item):
                log.debug('%s was not matched by content_match_filter: %s', installed_content_item, content_item_match_filter)
                continue

            # this is sort of the 'join' of installed_repository and installed_content
            content_info = {'path': installed_content_item.path,
                            'content_data': installed_content_item,
                            'installed_repository': installed_repository,
                            'version': installed_content_item.version,
                            }

            yield content_info


class InstalledContentItemDatabase(object):

    def __init__(self, installed_context=None):
        self.installed_context = installed_context

    # select content based on matching the installed namespace.repository and/or the content itself
    def select(self, repository_match_filter=None, content_match_filter=None):
        # ie, default to select * more or less
        repository_match_filter = repository_match_filter or matchers.MatchAll()
        content_match_filter = content_match_filter or matchers.MatchAll()

        roles_content_item_iterator = \
            installed_content_item_iterator(self.installed_context,
                                            content_item_type='roles',
                                            repository_match_filter=repository_match_filter,
                                            content_item_match_filter=content_match_filter)

        for matched_content_item in roles_content_item_iterator:
            yield matched_content_item
