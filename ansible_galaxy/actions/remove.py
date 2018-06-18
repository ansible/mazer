import logging

from ansible_galaxy.flat_rest_api.content import GalaxyContent
from ansible_galaxy import installed_content_db
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


# for remove don't match anything if nothing is specified
def match_none():
    return False


def remove(galaxy_context,
           match_filter=None,
           display_callback=None):

    match_filter = match_filter or match_none

    icdb = installed_content_db.InstalledContentDatabase(galaxy_context)

    for content_info in icdb.select(match_filter):
        log.debug('removing %s', content_info)
        content_info['content_data'].remove()

    return 0
