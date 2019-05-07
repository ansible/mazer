
import logging

from ansible_galaxy import installed_repository_db
from ansible_galaxy import matchers

log = logging.getLogger(__name__)


# galaxy_context.collections_path is empty
def test_installed_repository_db(galaxy_context):
    icdb = installed_repository_db.InstalledRepositoryDatabase(galaxy_context)

    for x in icdb.select():
        log.debug('x: %s', x)


# galaxy_context.collections_path is empty
def test_installed_repository_db_match_names(galaxy_context):
    icdb = installed_repository_db.InstalledRepositoryDatabase(galaxy_context)

    match_filter = matchers.MatchLabels(['foo.bar'])
    for x in icdb.select(match_filter):
        log.debug('x: %s', x)
