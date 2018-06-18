import glob
import logging
import os

from ansible_galaxy import content_db
from ansible_galaxy import exceptions
from ansible_galaxy import installed_repository_db

from ansible_galaxy.flat_rest_api.content import InstalledContent

log = logging.getLogger(__name__)


def match_all(galaxy_content):
    return True


class MatchContentNames(object):
    def __init__(self, names):
        self.names = names

    def __call__(self, other):
        return self.match(other)

    def match(self, other):
        log.debug('self.names: %s other.name: %s', self.names, other.name)
        return other.name in self.names


# need a content_type matcher?
def installed_namespace_role_iterator(namespace_path):

    namespaced_roles_dirs = glob.glob('%s/%s/*' % (namespace_path, 'roles'))
    for namespaced_roles_path in namespaced_roles_dirs:
        # full_content_paths.append(namespaced_roles_path)
        yield namespaced_roles_path


namespace_content_iterator_map = {'roles': installed_namespace_role_iterator}


def installed_namespace_iterator(content_path, content_type=None):
    try:
        # TODO: filter on any rules for what a namespace path looks like
        #       may one being 'somenamespace.somename' (a dot sep ns and name)
        #
        namespace_paths = os.listdir(content_path)
    except OSError as e:
        log.exception(e)
        raise exceptions.GalaxyError('The path %s did not exist', content_path)

    log.debug('namespace_paths for content_path=%s: %s', content_path, namespace_paths)

    for namespace_path in namespace_paths:
        namespace_full_path = os.path.join(content_path, namespace_path)
        # log.debug('namespace_full_path: %s', namespace_full_path)
        # log.debug('glob=%s', '%s/roles/*' % namespace_full_path)
        yield namespace_full_path


def installed_content_iterator(galaxy_context,
                               content_type=None,
                               repository_match_filter=None,
                               content_match_filter=None):

    # match_all works for all types
    content_match_filter = content_match_filter or match_all
    repository_match_filter = repository_match_filter or match_all
    # log.debug('locals: %s', locals())

    # TODO: make this into a Content iterator / database / name directory / index / etc

    content_type = content_type or 'roles'
    # full_content_paths = []

    content_path = galaxy_context.content_path
    # show all valid content in the content_path directory

    log.debug('content_path: %s', content_path)
    content_path = os.path.expanduser(content_path)

    # namespace_paths_iterator = installed_namespace_iterator(content_path)
    installed_repo_db = installed_repository_db.InstalledRepositoryDatabase(galaxy_context)

    # for x in repository_iterator.select():
    #    log.debug('repo: %s', x)

    # content_infos = []

    # for namespace_full_path in namespace_paths_iterator:
    for installed_repository in installed_repo_db.select(match_filter=repository_match_filter):
        installed_repository_full_path = installed_repository.path
        # log.debug('installed_repository_full_path: %s', installed_repository_full_path)

        if not repository_match_filter(installed_repository):
            log.debug('The repo_match_filter %s failed to match for %s', repository_match_filter, installed_repository)
            continue

        # since we will need a different iterator for each specific type of content, consult
        # a map of content_type->iterator_method however there is only a 'roles' iterator for now
        installed_repository_content_iterator_method = namespace_content_iterator_map.get(content_type)
        if installed_repository_content_iterator_method is None:
            continue

        installed_repository_content_iterator = installed_repository_content_iterator_method(installed_repository_full_path)

        for installed_content_full_path in installed_repository_content_iterator:
            # log.debug('installed_content_full_path: %s', installed_content_full_path)
            path_file = os.path.basename(installed_content_full_path)
            # log.debug('path_file / name: %s', path_file)

            # TODO: create and use a InstalledGalaxyContent
            gr = InstalledContent(galaxy_context, path_file, path=installed_content_full_path)

            # FIXME: not so much a kluge, but a sure sign that GalaxyContent.path
            #        (or its alias GalaxyContent.content_meta.path) have different meanings
            #        in diff parts of the code  (sometimes for the root dir where content lives
            #        (.ansible/content) sometimes for the path the dir to the content
            #        (.ansible/content/roles/test-role-a for ex)
            gr.content_meta.path = installed_content_full_path

    #         log.debug('gr: %s', gr)
    #        log.debug('gr.metadata: %s', gr.metadata)

            version = None

            log.debug('gr.install_info: %s', gr.install_info)

            if gr.metadata or gr.install_info:
                install_info = gr.install_info
                if install_info:
                    version = install_info.get("version", None)
                if not version:
                    version = "(unknown version)"
                # display_callback("- %s, %s" % (path_file, version))

            if not content_match_filter(gr):
                log.debug('%s was not matched by content_match_filter: %s', gr, content_match_filter)
                continue

            content_info = {'path': path_file,
                            'content_data': gr,
                            'installed_repository': installed_repository,
                            'version': version,
                            }

            yield content_info


class InstalledContentDatabase(content_db.ContentDatabase):
    database_type = 'base'

    def __init__(self, installed_context=None):
        self.installed_context = installed_context

    # select content based on matching the installed namespace.repository and/or the content itself
    def select(self, repository_match_filter=None, content_match_filter=None):
        # ie, default to select * more or less
        repository_match_filter = repository_match_filter or match_all
        content_match_filter = content_match_filter or match_all

        roles_content_iterator = installed_content_iterator(self.installed_context,
                                                            content_type='roles',
                                                            repository_match_filter=repository_match_filter,
                                                            content_match_filter=content_match_filter)

        for matched_content in roles_content_iterator:
            yield matched_content
