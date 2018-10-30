import datetime
import io
import logging

import yaml

from six import string_types

from ansible_galaxy import install_info
from ansible_galaxy.models.install_info import InstallInfo

log = logging.getLogger(__name__)

yaml_data1 = u'''
install_date: Tue Jul 17 14:41:59 2018
install_date_iso: 2018-07-17 14:41:59.229716
version: 0.1.0
'''


def test_load():
    yaml_fo = io.StringIO(initial_value=yaml_data1)
    install_info_ = install_info.load(yaml_fo)

    log.debug('install_info_: %s', install_info_)

    assert isinstance(install_info_, InstallInfo)

    assert str(install_info_.version) == '0.1.0'
    assert isinstance(install_info_.install_date_iso, datetime.datetime)
    assert isinstance(install_info_.install_date, string_types)


def test_load_string():
    install_info_ = install_info.load(yaml_data1)

    log.debug('install_info_: %s', install_info_)

    assert isinstance(install_info_, InstallInfo)

    assert str(install_info_.version) == '0.1.0'
    assert isinstance(install_info_.install_date_iso, datetime.datetime)
    assert isinstance(install_info_.install_date, string_types)


def test_load_from_filename(tmpdir):
    temp_dir = tmpdir.mkdir('mazer_content_install_info_unit_test')
    temp_file = temp_dir.join('.galaxy_install_info')
    temp_file.write(yaml_data1)

    log.debug('temp_file.strpath: %s', temp_file.strpath)

    install_info_ = install_info.load_from_filename(temp_file.strpath)

    log.debug('install_info_: %s', install_info_)

    assert isinstance(install_info_, InstallInfo)

    assert str(install_info_.version) == '0.1.0'
    assert isinstance(install_info_.install_date_iso, datetime.datetime)
    assert isinstance(install_info_.install_date, string_types)


def test_save(tmpdir):
    install_datetime = datetime.datetime.utcnow()
    install_info_ = InstallInfo.from_version_date(version='4.5.6',
                                                  install_datetime=install_datetime)
    log.debug('install_info: %s', install_info_)

    temp_dir = tmpdir.mkdir('mazer_content_install_info_unit_test')
    temp_file = temp_dir.join('.galaxy_install_info')
    install_info.save(install_info_.to_dict_version_strings(),
                      temp_file.strpath)

    log.debug('tmpfile: %s', temp_file)

    res = temp_file.read()
    log.debug('res: %s', res)

    reloaded = yaml.safe_load(res)

    assert isinstance(reloaded, dict)
    assert reloaded['version'] == '4.5.6'
    assert reloaded['install_date_iso'] == install_datetime

# TODO: test perms, etc
