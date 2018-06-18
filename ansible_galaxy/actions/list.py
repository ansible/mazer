
import logging

from ansible_galaxy import installed_content_db

log = logging.getLogger(__name__)


def match_all(galaxy_content):
    return True


def list(galaxy_context,
         match_filter=None,
         display_callback=None):

    match_filter = match_filter or match_all
    log.debug('locals: %s', locals())

    icdb = installed_content_db.InstalledContentDatabase(galaxy_context)

    for content_info in icdb.select(match_filter):
        content_dict = content_info.copy()
        repo = content_dict.pop('installed_repository')

        # revisit this output format once we get some feedback
        content_dict.update({'type': content_dict['content_data'].content_type,
                             'name': content_dict['content_data'].name,
                             # 'installed_repo_namespace': repo.namespace,
                             # 'installed_repo_name': repo.name,
                             # 'installed_repo_path': repo.path,
                             'installed_repo_id': '%s.%s' % (repo.namespace, repo.name),
                             })
        display_callback("repo={installed_repo_id}, type={type}, name={name}, version={version}".format(**content_dict))

    return 0
