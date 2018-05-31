
import logging
import os

from ansible_galaxy import exceptions
from ansible_galaxy.flat_rest_api.content import GalaxyContent

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


def list(galaxy_context,
         roles_path,
         match_filter=None,
         display_callback=None):

    match_filter = match_filter or match_all
    log.debug('locals: %s', locals())

    full_role_paths = []
    # show all valid roles in the roles_path directory
    for path in roles_path:
        role_path = os.path.expanduser(path)
        if not os.path.exists(role_path):
            raise exceptions.GalaxyError("- the path %s does not exist. Please specify a valid path with --roles-path" % role_path)
        elif not os.path.isdir(role_path):
            raise exceptions.GalaxyError("- %s exists, but it is not a directory. Please specify a valid path with --roles-path" % role_path)
        full_role_paths.append(role_path)

    log.debug('full_role_paths: %s', full_role_paths)

    content_infos = []

    for path in full_role_paths:
        path_files = os.listdir(role_path)

        for path_file in path_files:
            role_full_path = os.path.join(role_path, path_file)

            log.debug('role_full_path: %s', role_full_path)
            log.debug('path_file / name: %s', path_file)

            gr = GalaxyContent(galaxy_context, path_file, path=role_full_path)



            # FIXME: not so much a kluge, but a sure sign that GalaxyContent.path
            #        (or its alias GalaxyContent.content_meta.path) have different meanings
            #        in diff parts of the code  (sometimes for the root dir where content lives
            #        (.ansible/content) sometimes for the path the dir to the content
            #        (.ansible/content/roles/test-role-a for ex)
            gr.content_meta.path = role_full_path



            log.debug('gr: %s', gr)
            log.debug('gr.metadata: %s', gr.metadata)

            version = None

            log.debug('gr.install_info: %s', gr.install_info)

            if gr.metadata:
                install_info = gr.install_info
                if install_info:
                    version = install_info.get("version", None)
                if not version:
                    version = "(unknown version)"
                # display_callback("- %s, %s" % (path_file, version))

            if match_filter(gr):
                content_infos.append({'path': path_file,
                                      'content_data': gr,
                                      'version': version})

    log.debug('content_infos: %s', content_infos)
    for content_info in content_infos:
        display_callback("- {path}, {version}".format(**content_info))

    return 0
