import collections
import logging

from ansible_galaxy import installed_content_item_db
from ansible_galaxy import installed_repository_db
from ansible_galaxy import matchers

log = logging.getLogger(__name__)


def _list(galaxy_context,
          repository_spec_match_filter=None,
          list_content=False,
          display_callback=None):

    log.debug('list_content: %s', list_content)

    all_repository_match = repository_spec_match_filter or matchers.MatchAll()

    # We search for installed repos to list, and then display all the content in those installed repos
    icidb = installed_content_item_db.InstalledContentItemDatabase(galaxy_context)

    irdb = installed_repository_db.InstalledRepositoryDatabase(galaxy_context)

    # accumulate for api return
    repo_list = []

    for installed_repository in irdb.select(repository_spec_match_filter=all_repository_match):
        log.debug('installed_repo: %s', installed_repository)

        content_items = collections.defaultdict(list)

        # Find all the content items for this particular repo
        repository_match = matchers.MatchRepositorySpec([installed_repository.repository_spec])

        for content_info in icidb.select(repository_spec_match_filter=repository_match):
            content_dict = content_info.copy()

            content_item_type = content_dict['content_data'].content_item_type

            # revisit this output format once we get some feedback
            content_dict.update({'type': content_item_type,
                                 'name': content_dict['content_data'].name,
                                 # 'installed_repo_namespace': repo.namespace,
                                 # 'installed_repo_name': repo.name,
                                 # 'installed_repo_path': repo.path,
                                 # 'installed_repo_id': repo.repository_spec.label,
                                 'installed_repository': installed_repository,
                                 })

            content_items[content_item_type].append(content_dict)
            # content_item_list.append(content_dict)

        repo_dict = {'content_items': content_items,
                     'installed_repository': installed_repository}
        repo_list.append(repo_dict)

    for repo_item in repo_list:
        repo_msg = "repo={installed_repository.repository_spec.label}, type=repository, version={installed_repository.repository_spec.version}"
        display_callback(repo_msg.format(**repo_item))

        if not list_content:
            continue

        for content_item_type_key, content_items_data in repo_item['content_items'].items():
            content_msg = "repo={installed_repository.repository_spec.label}, type={type}, name={name}, " + \
                "version={installed_repository.repository_spec.version}"
            # content_msg = "    type={type}, name={name}, " + \
            #    "version={installed_repository.repository_spec.version}"

            # type_msg = "  {content_item_type}:"
            # display_callback(type_msg.format(content_item_type=content_item_type_key))

            log.debug('content_item: %s', content_items_data)
            log.debug('content_item_type_key: %s', content_item_type_key)

            for content_item_data in content_items_data:
                display_callback(content_msg.format(**content_item_data))
        # display_callback(msg.format(**content_dict))

    return repo_list


def list_action(galaxy_context,
                repository_spec_match_filter=None,
                list_content=False,
                display_callback=None):
    '''Run _list action and return an exit code suitable for process exit'''

    _list(galaxy_context,
          repository_spec_match_filter=repository_spec_match_filter,
          list_content=list_content,
          display_callback=display_callback)

    return 0
