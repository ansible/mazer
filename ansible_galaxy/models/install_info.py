import datetime
import logging

import attr
import semantic_version

from ansible_galaxy.utils.version import convert_string_to_semver

log = logging.getLogger(__name__)


@attr.s(frozen=True)
class InstallInfo(object):
    '''The info that is saved into the .galaxy_install_info file'''
    install_date = attr.ib()
    install_date_iso = attr.ib(type=datetime.datetime)

    version = attr.ib(type=semantic_version.Version, default=None,
                      converter=convert_string_to_semver)

    @classmethod
    def from_version_date(cls, version, install_datetime):
        inst = cls(version=version,
                   install_date_iso=install_datetime,
                   install_date=install_datetime.strftime('%c'))
        return inst

    def to_dict_version_strings(self):
        data = attr.asdict(self)

        if data.get('verison', '') is None:
            del data['version']

        # semantic_version.Version isnt yaml-able, so build a dict with
        # the Version replaced with a str version
        ver = data.get('version', '')
        if ver:
            data['version'] = str(ver)

        return data
