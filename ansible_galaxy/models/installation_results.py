import datetime
import logging

import attr

from ansible_galaxy.models.install_info import InstallInfo

log = logging.getLogger(__name__)


@attr.s(frozen=True)
class InstallationResults(object):
    install_info_path = attr.ib()
    install_info = attr.ib(type=InstallInfo)

    installed_to_path = attr.ib()
    installed_datetime = attr.ib(type=datetime.datetime)

    installed_files = attr.ib(factory=list)
