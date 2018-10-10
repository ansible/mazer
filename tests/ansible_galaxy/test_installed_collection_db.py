
import logging

from ansible_galaxy import installed_collection_db
from ansible_galaxy import matchers

log = logging.getLogger(__name__)


# galaxy_context.content_path is empty
def test_installed_collection_db(galaxy_context):
    icdb = installed_collection_db.InstalledCollectionDatabase(galaxy_context)

    for x in icdb.select():
        log.debug('x: %s', x)


# galaxy_context.content_path is empty
def test_installed_collection_db_match_names(galaxy_context):
    icdb = installed_collection_db.InstalledCollectionDatabase(galaxy_context)

    match_filter = matchers.MatchNames(['foo.bar'])
    for x in icdb.select(match_filter):
        log.debug('x: %s', x)
