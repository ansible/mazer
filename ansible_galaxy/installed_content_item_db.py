import glob
import itertools
import logging
import os

from ansible_galaxy import installed_repository_db
from ansible_galaxy import matchers
from ansible_galaxy.models.content_item import ContentItem

log = logging.getLogger(__name__)


def is_plugin_file(path):
    if path.endswith('__init__.py'):
        return False

    if path.endswith('__pycache__'):
        return False

    return True


def python_content_path_iterator(repository, content_item_sub_dir):
    '''For paths where python plugins live, filters out __init__.py'''

    return (x for x in glob.iglob('%s/%s/*' % (repository.path, content_item_sub_dir)) if is_plugin_file(x))


def is_plugin_dir(plugin_dir_path):
    '''Check plugins/ items to see if a potential plugin dir is a dir

    No other checks are used to determine if plugin_dir_path is actually a plugin dir'''
    if os.path.isdir(plugin_dir_path):
        if plugin_dir_path.endswith('__pycache__'):
            return False
        return True

    return False


def plugin_content_item_types(repository):
    '''Return all the subdirs in plugins/ assuming only plugin type dirs exist

    ie, this doesn't have preconceived notions of the possible plugin types'''
    plugins_dir = os.path.join(repository.path, 'plugins')
    try:
        res = [x for x in os.listdir(plugins_dir) if is_plugin_dir(os.path.join(plugins_dir, x))]
        return res
    except (OSError, IOError):
        # log.warning(e)
        return []


# need a content_type matcher?
def repository_content_iterator(repository, content_item_type, content_item_paths_iterator):

    for content_item_path in content_item_paths_iterator:
        repo_namespace = repository.repository_spec.namespace
        file_name = os.path.basename(content_item_path)

        # This assumes module and plugins with filenames with an extension will always
        # use the content item name as the pre-ext part of filename. That could change
        # in the future.
        content_item_name = os.path.splitext(file_name)[0]

        content_item = ContentItem(namespace=repo_namespace,
                                   name=content_item_name,
                                   path=file_name,
                                   content_item_type=content_item_type,
                                   version=repository.repository_spec.version)

        log.debug('Found %s "%s" at %s', content_item, content_item.name, file_name)
        yield content_item


def all_content_item_types_iterator(repository):
    all_content_iterators = [
        repository_content_iterator(repository,
                                    'roles',
                                    python_content_path_iterator(repository, 'roles')),
    ]

    for plugin_content_item_type in plugin_content_item_types(repository):
        plugin_iterator = repository_content_iterator(repository,
                                                      plugin_content_item_type,
                                                      python_content_path_iterator(repository,
                                                                                   os.path.join('plugins', plugin_content_item_type)))
        all_content_iterators.append(plugin_iterator)

    # chain all the iterables that generator ContentItems together
    return itertools.chain.from_iterable(all_content_iterators)


def installed_content_item_iterator(galaxy_context,
                                    namespace_match_filter=None,
                                    repository_spec_match_filter=None,
                                    content_item_match_filter=None,
                                    content_item_type=None):

    # match_all works for all types
    namespace_match_filter = namespace_match_filter or matchers.MatchAll()
    repository_spec_match_filter = repository_spec_match_filter or matchers.MatchAll()
    content_item_match_filter = content_item_match_filter or matchers.MatchAll()

    content_item_type = content_item_type or 'roles'

    installed_repo_db = installed_repository_db.InstalledRepositoryDatabase(galaxy_context)

    # for namespace_full_path in namespace_paths_iterator:
    for installed_repository in installed_repo_db.select(namespace_match_filter=namespace_match_filter,
                                                         repository_spec_match_filter=repository_spec_match_filter):
        log.debug('Found repository "%s" at %s', installed_repository.repository_spec.label, installed_repository.path)
        installed_repository_full_path = installed_repository.path

        if not repository_spec_match_filter(installed_repository):
            log.debug('The repository_match_filter %s failed to match for %s', repository_spec_match_filter, installed_repository)
            continue

        all_content_iterator = all_content_item_types_iterator(installed_repository)

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
    def select(self, repository_spec_match_filter=None, content_match_filter=None):
        # ie, default to select * more or less
        repository_spec_match_filter = repository_spec_match_filter or matchers.MatchAll()
        content_match_filter = content_match_filter or matchers.MatchAll()

        roles_content_item_iterator = \
            installed_content_item_iterator(self.installed_context,
                                            content_item_type='roles',
                                            repository_spec_match_filter=repository_spec_match_filter,
                                            content_item_match_filter=content_match_filter)

        for matched_content_item in roles_content_item_iterator:
            yield matched_content_item
