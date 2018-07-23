import logging

import attr


log = logging.getLogger(__name__)


@attr.s(frozen=True)
class ContentInstallInfo(object):
    '''The info that is saved into the .galaxy_install_info file'''
    install_date = attr.ib()
    install_date_iso = attr.ib()
    version = attr.ib()
