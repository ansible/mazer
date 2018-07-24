import logging

import attr


log = logging.getLogger(__name__)


@attr.s(frozen=True)
class InstallInfo(object):
    '''The info that is saved into the .galaxy_install_info file'''
    install_date = attr.ib()
    install_date_iso = attr.ib()
    version = attr.ib()

    @classmethod
    def from_version_date(cls, version, install_datetime):
        inst = cls(version=version,
                   install_date_iso=install_datetime,
                   install_date=install_datetime.strftime('%c'))
        return inst
