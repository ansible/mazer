import logging

from ansible_galaxy.flat_rest_api.content import GalaxyContent
from ansible_galaxy_cli import exceptions as cli_exceptions

log = logging.getLogger(__name__)


def remove_role(galaxy_context,
                role_name,
                display_callback=None):
    log.debug('looking for content %s to remove', role_name)

    role = GalaxyContent(galaxy_context, role_name)

    log.debug('content to remove: %s %s', role, type(role))

    try:
        if role.remove():
            display_callback('- successfully removed %s' % role_name)
        else:
            display_callback('- %s is not installed, skipping.' % role_name)
    except Exception as e:
        log.exception(e)
        raise cli_exceptions.GalaxyCliError("Failed to remove role %s: %s" % (role_name, str(e)))

    # FIXME: return code?  was always returning 0


def remove(galaxy_context,
           role_names,
           display_callback=None):

    for role_name in role_names:

        log.debug('remove_role %s', role_name)

        remove_role(galaxy_context,
                    role_names,
                    display_callback)
