
import logging
import os
import pprint


from ansible_galaxy import display
from ansible_galaxy import matchers
from ansible_galaxy import installed_content_db
from ansible_galaxy import installed_repository_db
from ansible_galaxy.utils.content_name import parse_content_name
from ansible_galaxy.utils.text import to_text

log = logging.getLogger(__name__)

SKIP_INFO_KEYS = ("name", "description", "readme_html", "related", "summary_fields", "average_aw_composite", "average_aw_score", "url")

REPO_TEMPLATE = """
label: {repo_label}
namespace: {repo_namespace}
name: {repo_name}
format: {repo_format}
latest_version: {repo_latest_version}
description: {repo_description}
scm: {repo_clone_url}

{repo_contents}"""

CONTENT_TEMPLATE = """    content_name: {content_name}
    content_type: {content_type}
    description: {content_description}
"""


INSTALLED_CONTENT_TEMPLATE = """
name: {name}
version: {version}"""


# FIXME: format?
def _repr_remote_repo(remote_data):
    log.debug('remote_data: %s', remote_data)
    # print(remote_data)

    # flatten some info for format simplicity
    repo_namespace = remote_data['summary_fields']['namespace']['name']
    repo_name = remote_data['name']
    remote_data['repo_label'] = "{namespace}.{name}".format(namespace=repo_namespace, name=repo_name)
    remote_data['repo_namespace'] = remote_data['summary_fields']['namespace']['name']
    remote_data['repo_description'] = remote_data['description']
    remote_data['repo_clone_url'] = remote_data['clone_url']
    # remote_data['repo_name'] = remote_data['summary_fields']['repository']['original_name']
    remote_data['repo_name'] = remote_data['name']
    remote_data['repo_format'] = remote_data['format']

    content_info_parts = []
    content_objects = remote_data['summary_fields']['content_objects']
    for content_object in content_objects:
        content_data = {}
        content_data['content_name'] = content_object['name']
        content_data['content_type'] = content_object['content_type']
        content_data['content_description'] = content_object['description']

        content_str = CONTENT_TEMPLATE.format(**content_data)
        log.debug('content_str: %s', content_str)
        content_info_parts.append(content_str)

    versions = remote_data['summary_fields']['versions']
    try:
        latest_version = versions[0].get('version', 'N/A')
    except IndexError:
        latest_version = ""

    remote_data['repo_latest_version'] = latest_version

    remote_data['repo_contents'] = '\n'.join(content_info_parts)

    log.debug(pprint.pformat(remote_data))
    return REPO_TEMPLATE.format(**remote_data)
    # return pprint.pformat(content_info)


def _repr_installed_repo(installed_repo):
    lines = []
    lines.append('installed_path: %s' % installed_repo.path)
    return '\n'.join(lines)


def _repr_installed_content(installed_content):
    # print('i_d: %s' % installed_content)
    installed_data = {'name': installed_content['installed_repository'].name,
                      'version': installed_content['version'],
                      'path': installed_content['installed_repository'].path}
    return INSTALLED_CONTENT_TEMPLATE.format(**installed_data)


# TODO: move to a repr for Role?
def _repr_role_info(role_info):

    text = [u"", u"Role: %s" % to_text(role_info['name'])]
    text.append(u"\tdescription: %s" % role_info.get('description', ''))

    for k in sorted(role_info.keys()):

        if k in SKIP_INFO_KEYS:
            continue

        if isinstance(role_info[k], dict):
            text.append(u"\t%s:" % (k))
            for key in sorted(role_info[k].keys()):
                if key in SKIP_INFO_KEYS:
                    continue
                text.append(u"\t\t%s: %s" % (key, role_info[k][key]))
        else:
            text.append(u"\t%s: %s" % (k, role_info[k]))

    return u'\n'.join(text)


def info_content_specs(galaxy_context,
                       api,
                       content_specs,
                       display_callback=None,
                       offline=None):

    output = ''
    online = not offline

    display_callback = display_callback or display.display_callback

    # log.debug('base_content_path: %s', base_content_path)
    # content_path = galaxy_context.content_path

    offline = offline or False

    icdb = installed_content_db.InstalledContentDatabase(galaxy_context)
    irdb = installed_repository_db.InstalledRepositoryDatabase(galaxy_context)

    not_installed = []

    labels_to_match = []

    for content_spec in content_specs:
        galaxy_namespace, repo_name, content_name = parse_content_name(content_spec)

        log.debug('content_spec=%s', content_spec)
        log.debug('galaxy_username=%s', galaxy_namespace)
        log.debug('repo_name=%s', repo_name)
        log.debug('content_name=%s', content_name)

        repo_name = repo_name or content_name
        log.debug('repo_name2=%s', repo_name)

        if online:
            # remote_data = api.lookup_content_by_name(galaxy_namespace, repo_name, content_name)
            remote_data = api.lookup_repo_by_name(galaxy_namespace, repo_name)
            display_callback(_repr_remote_repo(remote_data))

        label_to_match = '%s.%s' % (galaxy_namespace, repo_name)
        labels_to_match.append((label_to_match, content_spec))

    # matcher = matchers.MatchNamespacesOrLabels([label_and_spec[0] for label_and_spec in labels_to_match])
    matcher = matchers.MatchContentSpec([label_and_spec[1] for label_and_spec in labels_to_match])

    matched_repos = irdb.select(repository_match_filter=matcher)

    # matched_contents = icdb.select(repository_match_filter=matcher)
    # log.debug('matched_contents: %s', list(matched_contents))

    # content_path = os.path.join(content_path, '%s.%s' % (galaxy_namespace, repo_name))

    remote_data = False

    for matched_repo in matched_repos:
        display_callback(_repr_installed_repo(matched_repo))
        log.debug(matched_repo)

        #for matched_content in matched_contents:
        #    display_callback(_repr_installed_content(matched_content))


    # FIXME

    return



    # TODO: split 'info' action into 'info about installed repos' and 'info from galaxy about a repo'
    if not offline:
        # remote_data = api.lookup_content_by_name(galaxy_namespace, repo_name, content_name)
        remote_data = api.lookup_repo_by_name(galaxy_namespace, repo_name)
        display_callback(_repr_remote_repo(remote_data))
    else:
        for matched_content in matched_contents:
            display_callback(_repr_installed_content(matched_content))

    # role_spec = yaml_parse({'role': role})
    # if role_spec:
    #     role_info.update(role_spec)

    # not_installed =
    # data = self._display_role_info(content_info)
    # FIXME: This is broken in both 1.9 and 2.0 as
    # _display_role_info() always returns something

    display_callback(output)

    if not_installed:
        display_callback('These repos were not installed: %s' % ', '.join(sorted(not_installed)))

    return 0
