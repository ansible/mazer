import glob
import logging
import os

from ansible_galaxy import content_db
from ansible_galaxy import exceptions

from ansible_galaxy.flat_rest_api.content import InstalledContent

log = logging.getLogger(__name__)


def match_all(galaxy_content):
    return True


class MatchNames(object):
    def __init__(self, names):
        self.names = names

    def __call__(self, other):
        return self.match(other)

    def match(self, other):
        log.debug('self.names: %s other.name: %s', self.names, other.name)
        return other.name in self.names


def installed_namespace_iterator(content_path):
    try:
        # TODO: filter on any rules for what a namespace path looks like
        #       may one being 'somenamespace.somename' (a dot sep ns and name)
        #
        namespace_paths = os.listdir(content_path)
    except OSError as e:
        log.exception(e)
        raise exceptions.GalaxyError('The path %s did not exist', content_path)

    log.debug('namespace_paths: %s', namespace_paths)

    for namespace_path in namespace_paths:
        namespace_full_path = os.path.join(content_path, namespace_path)
        # log.debug('namespace_full_path: %s', namespace_full_path)
        # log.debug('glob=%s', '%s/roles/*' % namespace_full_path)
        namespaced_roles_dirs = glob.glob('%s/roles/*' % namespace_full_path)
        # log.debug('namespaced_roles_paths: %s', namespaced_roles_dirs)

        for namespaced_roles_path in namespaced_roles_dirs:
            # full_content_paths.append(namespaced_roles_path)
            yield namespaced_roles_path


def installed_content_iterator(galaxy_context,
                               content_type=None,
                               match_filter=None):

    match_filter = match_filter or match_all
    log.debug('locals: %s', locals())

    # TODO: make this into a Content iterator / database / name directory / index / etc

    content_type = content_type or 'roles'
    full_content_paths = []

    content_path = galaxy_context.content_path
    # show all valid content in the content_path directory

    log.debug('content_path: %s', content_path)
    content_path = os.path.expanduser(content_path)

    namespace_paths_iterator = installed_namespace_iterator(content_path)

    content_infos = []

    for content_full_path in namespace_paths_iterator:
        log.debug('content_full_path: %s', content_full_path)
        path_file = os.path.basename(content_full_path)
        # log.debug('path_file / name: %s', path_file)

        # TODO: create and use a InstalledGalaxyContent
        gr = InstalledContent(galaxy_context, path_file, path=content_full_path)

        # FIXME: not so much a kluge, but a sure sign that GalaxyContent.path
        #        (or its alias GalaxyContent.content_meta.path) have different meanings
        #        in diff parts of the code  (sometimes for the root dir where content lives
        #        (.ansible/content) sometimes for the path the dir to the content
        #        (.ansible/content/roles/test-role-a for ex)
        gr.content_meta.path = content_full_path

        log.debug('gr: %s', gr)
        log.debug('gr.metadata: %s', gr.metadata)

        version = None

        log.debug('gr.install_info: %s', gr.install_info)

        if gr.metadata or gr.install_info:
            install_info = gr.install_info
            if install_info:
                version = install_info.get("version", None)
            if not version:
                version = "(unknown version)"
            # display_callback("- %s, %s" % (path_file, version))

        if match_filter(gr):
            content_info = {'path': path_file,
                            'content_data': gr,
                            'version': version,
                            }

            yield content_info


class InstalledContentDatabase(content_db.ContentDatabase):
    database_type = 'base'

    def __init__(self, installed_context=None):
        self.installed_context = installed_context

    # where clause being some sort of matcher object
    def select(self, match_filter=None):
        # ie, default to select * more or less
        match_filter = match_filter or match_all

        roles_content_iterator = installed_content_iterator(self.installed_context,
                                                            content_type='roles',
                                                            match_filter=match_filter)

        for matched_content in roles_content_iterator:
            yield matched_content
