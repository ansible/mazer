
import glob
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
    content_paths = roles_path

    for content_path_ in content_paths:
        log.debug('content_path_: %s', content_path_)
        content_path = os.path.expanduser(content_path_)
        namespace_paths = os.listdir(content_path)
        log.debug('namespace_paths: %s', namespace_paths)

        for namespace_path in namespace_paths:
            namespace_full_path = os.path.join(content_path, namespace_path)
            # log.debug('namespace_full_path: %s', namespace_full_path)
            # log.debug('glob=%s', '%s/roles/*' % namespace_full_path)
            namespaced_roles_dirs = glob.glob('%s/roles/*' % namespace_full_path)
            # log.debug('namespaced_roles_paths: %s', namespaced_roles_dirs)

            for namespaced_roles_path in namespaced_roles_dirs:
                full_role_paths.append(namespaced_roles_path)

    log.debug('full_role_paths: %s', full_role_paths)

    content_infos = []

    for role_full_path in full_role_paths:
        log.debug('role_full_path: %s', role_full_path)
        path_file = os.path.basename(role_full_path)
        # log.debug('path_file / name: %s', path_file)

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
                                  'version': version,
                                  })

    log.debug('content_infos: %s', content_infos)
    for content_info in content_infos:
        display_callback("- {path}, {version}".format(**content_info))

    return 0
