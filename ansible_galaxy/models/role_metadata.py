import logging

import attr


log = logging.getLogger(__name__)


@attr.s(frozen=True)
class RoleMetadata(object):
    '''The info that is found in a role meta/main.yml file'''
    name = attr.ib(default=None)

    author = attr.ib(default=None)
    description = attr.ib(default=None)
    company = attr.ib(default=None)
    license = attr.ib(default=None)

    # behaviorial
    min_ansible_version = attr.ib(default=None, converter=str)
    min_ansible_container_version = attr.ib(default=None, converter=str)
    allow_duplicates = attr.ib(default=False)

    issue_tracker = attr.ib(default=None)
    github_branch = attr.ib(default=None)

    # TODO: validate list items are text
    galaxy_tags = attr.ib(factory=list)

    # TODO: a Platform model if needed
    platforms = attr.ib(factory=list)

    cloud_platforms = attr.ib(factory=list)

    # TODO: a role/content Dependency model
    dependencies = attr.ib(factory=list)
