import logging

import attr

log = logging.getLogger(__name__)


@attr.s(frozen=True)
class MigrateRoleContext(object):
    role_path = attr.ib(validator=attr.validators.instance_of(str))
    output_path = attr.ib(validator=attr.validators.instance_of(str))
    output_force = attr.ib(default=False, validator=attr.validators.instance_of(bool))

    # roles always have a name, but not a namespace
    role_name = attr.ib(default=None)

    # collections always have namespace and name
    collection_namespace = attr.ib(default=None)
    collection_name = attr.ib(default=None)
    collection_version = attr.ib(default=None)
    # Note: Not validating this as valid spdx here, collection_info
    #       will do that later
    collection_license = attr.ib(default=None)
