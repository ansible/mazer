import glob
import logging
import os

from ansible_galaxy import installed_repository_db
from ansible_galaxy import matchers
from ansible_galaxy.models.content_item import ContentItem

log = logging.getLogger(__name__)


# need a content_type matcher?
def installed_collection_role_iterator(collection_path):

    collection_roles_dirs = glob.glob('%s/%s/*' % (collection_path, 'roles'))
    for collection_roles_path in collection_roles_dirs:
        # full_content_paths.append(namespaced_roles_path)
        # log.debug('rrp: %s', collection_roles_path)
        yield collection_roles_path


installed_collection_content_iterator_map = {'roles': installed_collection_role_iterator}


def installed_content_item_iterator(galaxy_context,
                                    namespace_match_filter=None,
                                    collection_match_filter=None,
                                    content_match_filter=None,
                                    content_item_type=None):

    # match_all works for all types
    namespace_match_filter = namespace_match_filter or matchers.MatchAll()
    collection_match_filter = collection_match_filter or matchers.MatchAll()
    content_match_filter = content_match_filter or matchers.MatchAll()

    content_item_type = content_item_type or 'roles'

    installed_coll_db = installed_repository_db.InstalledRepositoryDatabase(galaxy_context)

    # for namespace_full_path in namespace_paths_iterator:
    for installed_collection in installed_coll_db.select(namespace_match_filter=namespace_match_filter,
                                                         collection_match_filter=collection_match_filter):
        log.debug('Found collection "%s" at %s', installed_collection.content_spec.label, installed_collection.path)
        installed_collection_full_path = installed_collection.path

        if not collection_match_filter(installed_collection):
            log.debug('The collection_match_filter %s failed to match for %s', collection_match_filter, installed_collection)
            continue

        # since we will need a different iterator for each specific type of content, consult
        # a map of content_type->iterator_method however there is only a 'roles' iterator for now
        installed_collection_content_iterator_method = \
            installed_collection_content_iterator_map.get(content_item_type)

        if installed_collection_content_iterator_method is None:
            continue

        installed_collection_content_iterator = installed_collection_content_iterator_method(installed_collection_full_path)

        log.debug('Looking for %s in collection at %s', content_item_type, installed_collection_full_path)
        for installed_content_full_path in installed_collection_content_iterator:

            repo_namespace = installed_collection.content_spec.namespace
            path_file = os.path.basename(installed_content_full_path)

            gr = ContentItem(namespace=repo_namespace, name=path_file,
                             path=installed_content_full_path,
                             content_item_type=content_item_type,
                             version=installed_collection.content_spec.version)

            log.debug('Found %s "%s" at %s', gr, gr.name, installed_content_full_path)

            version = None

            if not content_match_filter(gr):
                log.debug('%s was not matched by content_match_filter: %s', gr, content_match_filter)
                continue

            # this is sort of the 'join' of installed_collection and installed_content
            content_info = {'path': path_file,
                            'content_data': gr,
                            'installed_collection': installed_collection,
                            'version': version,
                            }

            yield content_info


class InstalledContentItemDatabase(object):

    def __init__(self, installed_context=None):
        self.installed_context = installed_context

    # select content based on matching the installed namespace.collection and/or the content itself
    def select(self, collection_match_filter=None, content_match_filter=None):
        # ie, default to select * more or less
        collection_match_filter = collection_match_filter or matchers.MatchAll()
        content_match_filter = content_match_filter or matchers.MatchAll()

        roles_content_iterator = \
            installed_content_item_iterator(self.installed_context,
                                            content_item_type='roles',
                                            collection_match_filter=collection_match_filter,
                                            content_match_filter=content_match_filter)

        for matched_content in roles_content_iterator:
            yield matched_content
