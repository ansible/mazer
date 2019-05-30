import collections
import logging

from ansible_galaxy import installed_content_item_db
from ansible_galaxy import installed_repository_db
from ansible_galaxy import matchers
from ansible_galaxy import yaml_persist

log = logging.getLogger(__name__)


class OutputFormat(object):
    HUMAN = 'human'
    LOCKFILE = 'lockfile'
    LOCKFILE_FREEZE = 'lockfile_freeze'
    FULLY_QUALIFIED = 'fully_qualified'


def format_as_lockfile(repo_list, lockfile_freeze=False):
    '''For a given repo_list, return the string content of the lockfile that matches'''

    if not repo_list:
        return ''

    collections_deps = {}
    for repo_item in repo_list:
        label = "{installed_repository.repository_spec.label}".format(**repo_item)
        version_spec = '*'

        if lockfile_freeze:
            version_spec = "=={installed_repository.repository_spec.version}".format(**repo_item)

        collections_deps[label] = version_spec

    buf = yaml_persist.safe_dump(collections_deps, None, default_flow_style=False)

    return buf.strip()


def display_for_human(repo_list, list_content, display_callback):
    '''Display installed collections in a format readable but probably not prefered by some humans'''

    INDENT = ' '
    for repo_item in repo_list:
        repo_msg = "{installed_repository.repository_spec.ns_n_v}"
        display_callback(repo_msg.format(**repo_item))

        if not list_content:
            continue

        for content_item_type_key, content_items_data in repo_item['content_items'].items():
            content_type_msg = "{indent:2}- {content_item_type}".format(content_item_type=content_item_type_key,
                                                                        indent=INDENT)

            display_callback(content_type_msg)

            content_msg = "{indent:4}- {name}"
            for content_item_data in content_items_data:
                display_callback(content_msg.format(indent=INDENT, name=content_item_data['name']))


def display_fully_qualified(repo_list, list_content, display_callback):
    '''Display installed collections in a format more or less like they would be referenced in a playbook'''

    INDENT = ' '
    for repo_item in repo_list:
        repo_msg = "{installed_repository.repository_spec.ns_n_v}"
        display_callback(repo_msg.format(**repo_item))

        if not list_content:
            continue

        for content_item_type_key, content_items_data in repo_item['content_items'].items():
            content_type_msg = "{indent:2}- {content_item_type}".format(content_item_type=content_item_type_key,
                                                                        indent=INDENT)

            display_callback(content_type_msg)

            content_msg = "{indent:4}- {installed_repository.repository_spec.label}.{name}"
            for content_item_data in content_items_data:
                content_item_data['indent'] = INDENT
                display_callback(content_msg.format(**content_item_data))

                # show python paths for plugins
                if content_item_data['is_plugin']:
                    python_path_msg = "{indent:6}- (python path) ansible_collections.{installed_repository.repository_spec.label}.plugins.{type}.{name}"
                    content_item_data['indent'] = INDENT
                    display_callback(python_path_msg.format(**content_item_data))


def _list(galaxy_context,
          repository_spec_match_filter=None,
          list_content=False,
          output_format=None,
          display_callback=None):

    output_format = output_format or OutputFormat.HUMAN

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
                                 'is_plugin': content_dict['content_data'].is_plugin,
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

    if output_format == OutputFormat.LOCKFILE:
        output = format_as_lockfile(repo_list,
                                    lockfile_freeze=False)
        display_callback(output)

    elif output_format == OutputFormat.LOCKFILE_FREEZE:
        output = format_as_lockfile(repo_list,
                                    lockfile_freeze=True)
        display_callback(output)

    elif output_format == OutputFormat.FULLY_QUALIFIED:
        display_fully_qualified(repo_list, list_content, display_callback)
    else:
        display_for_human(repo_list, list_content, display_callback)

    return repo_list


def list_action(galaxy_context,
                repository_spec_match_filter=None,
                list_content=False,
                lockfile_format=False,
                lockfile_freeze=False,
                output_format=None,
                display_callback=None):
    '''Run _list action and return an exit code suitable for process exit'''

    output_format = output_format or OutputFormat.HUMAN
    if lockfile_format:
        output_format = OutputFormat.LOCKFILE
    if lockfile_freeze:
        output_format = OutputFormat.LOCKFILE_FREEZE

    output_format = OutputFormat.FULLY_QUALIFIED

    _list(galaxy_context,
          repository_spec_match_filter=repository_spec_match_filter,
          list_content=list_content,
          output_format=output_format,
          display_callback=display_callback)

    return 0
