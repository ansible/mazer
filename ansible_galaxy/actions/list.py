
import logging

from ansible_galaxy import installed_content_db

log = logging.getLogger(__name__)


def match_all(galaxy_content):
    return True


def list(galaxy_context,
         roles_path,
         match_filter=None,
         display_callback=None):

    match_filter = match_filter or match_all
    log.debug('locals: %s', locals())

    icdb = installed_content_db.InstalledContentDatabase(galaxy_context)

    for content_info in icdb.select(match_filter):
        log.debug('content_info: %s', content_info)
        display_callback("- {path}, {version}".format(**content_info))

    return 0
