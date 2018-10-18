import logging

from ansible_galaxy import collection
from ansible_galaxy import installed_repository_db
from ansible_galaxy import matchers
from ansible_galaxy_cli import exceptions as cli_exceptions

log = logging.getLogger(__name__)


def remove_collection(installed_collection,
                      display_callback=None):
    log.debug('looking for content %s to remove', installed_collection)

    log.debug('content to remove: %s %s', installed_collection, type(installed_collection))

    try:
        res = collection.remove(installed_collection)
        if res:
            display_callback('- successfully removed %s' % installed_collection.label)
        else:
            display_callback('- %s is not installed, skipping.' % installed_collection.label)
    except Exception as e:
        log.exception(e)
        raise cli_exceptions.GalaxyCliError("Failed to remove installed collection %s: %s" %
                                            (installed_collection.label, str(e)))

    # FIXME: return code?  was always returning 0


def remove(galaxy_context,
           collection_match_filter=None,
           display_callback=None):

    collection_match_filter = collection_match_filter or matchers.MatchNone()

    icdb = installed_repository_db.InstalledRepositoryDatabase(galaxy_context)

    for matched_collection in icdb.select(collection_match_filter=collection_match_filter):
        log.debug('removing %s', matched_collection)
        # content_info['content_data'].remove()
        remove_collection(matched_collection,
                          display_callback=display_callback)

    return 0
