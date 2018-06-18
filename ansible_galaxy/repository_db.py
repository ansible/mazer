
import logging

from ansible_galaxy import exceptions
log = logging.getLogger(__name__)


# a base 'database' interface for querying info
# about galaxy content repositories
# (listing it, looking up a specific
# content, getting info about it, etc)
#
# One impl will be for locally installed content repos.
# Another will be for content repos available in Galaxy.
# Another would be a composite db combining multiple
# Galaxy's

# TODO: args for table/where_clause
class DataSourceUnknownTable(exceptions.GalaxyError):
    pass


# TODO: make this an AbstractBaseClass
class RepositoryDatabase(object):
    database_type = 'base'

    # where clause being some sort of matcher object
    def select(self, where_clause):
        # i
        raise DataSourceUnknownTable(where_clause)
