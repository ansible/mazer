
import attr


@attr.s(frozen=True)
class CollectionsLock(object):
    '''The collections "lock" (ie, manifest) used with --colleections-lock'''

    dependencies = attr.ib(factory=list, validator=attr.validators.instance_of(list))
