import logging

from ansible_galaxy import repository
from ansible_galaxy import installed_repository_db
from ansible_galaxy import matchers
from ansible_galaxy_cli import exceptions as cli_exceptions

log = logging.getLogger(__name__)


def remove_repository(installed_repository,
                      display_callback=None):
    log.debug('looking for repository %s to remove', installed_repository)

    log.debug('repository to remove: %s %s', installed_repository, type(installed_repository))

    try:
        res = repository.remove(installed_repository)
        if res:
            display_callback('- successfully removed %s' % installed_repository.label)
        else:
            display_callback('- %s is not installed, skipping.' % installed_repository.label)
    except Exception as e:
        log.exception(e)
        raise cli_exceptions.GalaxyCliError("Failed to remove installed repository %s: %s" %
                                            (installed_repository.label, str(e)))

    # FIXME: return code?  was always returning 0


def remove(galaxy_context,
           repository_spec_match_filter=None,
           display_callback=None):

    repository_spec_match_filter = repository_spec_match_filter or matchers.MatchNone()

    irdb = installed_repository_db.InstalledRepositoryDatabase(galaxy_context)

    for matched_repository in irdb.select(repository_spec_match_filter=repository_spec_match_filter):
        log.debug('removing %s', matched_repository)
        # content_info['content_data'].remove()
        remove_repository(matched_repository,
                          display_callback=display_callback)

    return 0
