from ansible_galaxy.utils import attr_utils
import attr


@attr.s(frozen=True)
class CollectionsLockfile(object):
    '''Represents the data in a collections lock yaml file.'''

    dependencies = attr.ib(factory=dict,
                           validator=attr.validators.instance_of(dict),
                           converter=attr_utils.convert_none_to_empty_dict)
