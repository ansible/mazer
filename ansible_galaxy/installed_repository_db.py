import logging
import os

from ansible_galaxy import content_spec_parse
from ansible_galaxy import exceptions
from ansible_galaxy import repository_db
from ansible_galaxy.models.content_repository import ContentRepository

log = logging.getLogger(__name__)


def repository_match_all(content_repository):
    return True


class MatchRepositoryNames(object):
    def __init__(self, names):
        self.names = names

    def __call__(self, other):
        return self.match(other)

    def match(self, other):
        log.debug('self.names: %s other.name: %s', self.names, other.name)
        return other.name in self.names


def installed_repository_iterator(galaxy_context,
                                  match_filter=None):

    content_path = galaxy_context.content_path

    try:
        # TODO: filter on any rules for what a namespace path looks like
        #       may one being 'somenamespace.somename' (a dot sep ns and name)
        #
        namespace_paths = os.listdir(content_path)
    except OSError as e:
        log.exception(e)
        raise exceptions.GalaxyError('The path %s did not exist', content_path)

    log.debug('namespace_paths for content_path=%s: %s', content_path, namespace_paths)

    for namespace_path in namespace_paths:

        # use the default 'local' style content_spec_parse and name resolver
        spec_data = content_spec_parse.spec_data_from_string(namespace_path)

        namespace_full_path = os.path.join(content_path, namespace_path)
        content_repository = ContentRepository(namespace=spec_data.get('namespace'),
                                               name=spec_data.get('name'),
                                               path=namespace_full_path)

        # if names
        if match_filter(content_repository):
            # log.debug('namespace_full_path: %s', namespace_full_path)
            # log.debug('glob=%s', '%s/roles/*' % namespace_full_path)
            # yield namespace_full_path
            yield content_repository


class InstalledRepositoryDatabase(repository_db.RepositoryDatabase):
    database_type = 'base'

    def __init__(self, installed_context=None):
        self.installed_context = installed_context

    # where clause being some sort of matcher object
    def select(self, match_filter=None):
        # ie, default to select * more or less
        repository_match_filter = match_filter or repository_match_all

        installed_repositories = installed_repository_iterator(self.installed_context,
                                                               match_filter=repository_match_filter)

        for matched_repository in installed_repositories:
            yield matched_repository
