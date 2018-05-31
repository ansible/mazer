
import logging
import os

from ansible_galaxy import exceptions
from ansible_galaxy.flat_rest_api.content import GalaxyContent

log = logging.getLogger(__name__)


def list(galaxy_context,
         roles_path,
         display_callback=None):

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
            log.debug('path_file: %s', path_file)

            gr = GalaxyContent(galaxy_context, path_file, path=role_full_path)

            log.debug('gr: %s', gr)
            log.debug('gr.metadata: %s', gr.metadata)

            version = None

            if gr.metadata:
                install_info = gr.install_info
                if install_info:
                    version = install_info.get("version", None)
                if not version:
                    version = "(unknown version)"
                display_callback("- %s, %s" % (path_file, version))

            content_infos.append({'path': path_file,
                                  'content_data': gr,
                                  'version': version})

    log.debug('content_infos: %s', content_infos)
    for content_info in content_infos:
        display_callback("- {path}, {version}".format(**content_info))

    return 0
