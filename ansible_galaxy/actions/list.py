
import logging

from ansible_galaxy import installed_content_item_db
from ansible_galaxy import matchers

log = logging.getLogger(__name__)


def _list(galaxy_context,
          collection_match_filter=None,
          display_callback=None):

    collection_match_filter = collection_match_filter or matchers.MatchAll()

    # We search for installed repos to list, and then display all the content in those installed repos
    icidb = installed_content_item_db.InstalledContentItemDatabase(galaxy_context)

    repo_list = []
    for content_info in icidb.select(collection_match_filter=collection_match_filter):
        content_dict = content_info.copy()
        collection = content_dict.pop('installed_collection')

        # revisit this output format once we get some feedback
        content_dict.update({'type': content_dict['content_data'].content_item_type,
                             'name': content_dict['content_data'].name,
                             # 'installed_repo_namespace': repo.namespace,
                             # 'installed_repo_name': repo.name,
                             # 'installed_repo_path': repo.path,
                             # 'installed_repo_id': repo.content_spec.label,
                             'installed_collection': collection,
                             })

        display_callback("repo={installed_collection.content_spec.label}, type={type}, name={name}, version={version}".format(**content_dict))

        repo_list.append(content_dict)

    return repo_list


def list(galaxy_context,
         collection_match_filter=None,
         display_callback=None):
    '''Run _list action and return an exit code suitable for process exit'''

    _list(galaxy_context,
          collection_match_filter=collection_match_filter,
          display_callback=display_callback)

    return 0
