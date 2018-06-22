
import logging

import pytest

from ansible_galaxy import content_version
from ansible_galaxy import exceptions

log = logging.getLogger(__name__)


def test_get_content_version_none():
    ret = content_version.get_content_version({}, None, [], None)
    log.debug('ret=%s', ret)

    assert ret == 'master'


def test_get_content_version_devel_version_no_content_versions():
    try:
        content_version.get_content_version({}, 'devel', [], None)
    except exceptions.GalaxyError:
        return

    assert False, 'Excepted a GalaxyError here since there are no content versions and "devel" is not in []'


@pytest.mark.xfail
def test_get_content_version_prod_version_in_content_versions():
    ret = content_version.get_content_version({}, 'prod', content_versions_147, None)
    log.debug('ret=%s', ret)

    assert ret == 'prod'


raw_content_versions_147 = [
    {
        "id": 126,
        "name": "2.3.7",
        "release_date": "2018-05-01T12:10:16-04:00",
        "url": "",
        "related": {},
        "summary_fields": {},
        "created": "2018-05-01T16:11:41.473282Z",
        "modified": "2018-05-01T16:11:42.110659Z",
        "active": True
    },
    {
        "id": 127,
        "name": "2.3.6",
        "release_date": "2018-05-01T11:54:19-04:00",
        "url": "",
        "related": {},
        "summary_fields": {},
        "created": "2018-05-01T16:11:42.114698Z",
        "modified": "2018-05-01T16:11:42.427811Z",
        "active": True
    },
]
# FIXME: current version compare excepts if a number and letter are compared
#    {
#        "id": 128,
#        "name": "prod",
#        "release_date": "2018-05-01T11:54:19-04:00",
#        "url": "",
#        "related": {},
#        "summary_fields": {},
#        "created": "2018-05-01T16:11:42.114698Z",
#        "modified": "2018-05-01T16:11:42.427811Z",
#        "active": True
#    }

content_versions_147 = [a.get('name') for a in raw_content_versions_147 if a.get('name', None)]
content_versions_v = content_versions_147 + ['v1.0.0', 'v3.0.0', 'v0.0.0']
content_versions_no_v = content_versions_147 + ['1.0.0', '3.0.0', '0.0.0']
content_versions_1_0_v_and_no_v = ['1.0.0', 'v1.0.0']
content_versions_v_and_no_v = content_versions_147 + content_versions_1_0_v_and_no_v

content_versions_boring = ['0.0.1', '0.0.11', '0.5.1', '0.99.0', '1.0.0', '2.0.0', '3.0.0']
content_versions_alphanumeric_post = ['0.0.1', '0.0.2a']
content_versions_alphanumeric = ['1', 'a']
versions_1_0_0_latest = ['0.0.0', '0.1', '0.5.5.5.5.5', '1.0.0']

content_versions_map = {
    '147': content_versions_147,
    'v': content_versions_v,
    'no_v': content_versions_no_v,
    '1_0_v_and_no_v': content_versions_1_0_v_and_no_v,
    'v_and_no_v': content_versions_v_and_no_v,
    'boring': content_versions_boring,
    '1_0_0_latest': versions_1_0_0_latest,
    'empty': [],
    # 'alphanumeric': content_versions_alphanumeric,
}

test_data = [
    {'ask': None, 'vid': 'empty', 'exp': 'master'},
    {'ask': 'v1.0.0', 'vid': 'v', 'exp': 'v1.0.0'},
    {'ask': 'v1.0.0', 'vid': 'no_v', 'exp': '1.0.0'},
    {'ask': '1.0.0', 'vid': 'v', 'exp': 'v1.0.0'},
    {'ask': '1.0.0', 'vid': 'no_v', 'exp': '1.0.0'},
    # {'ask': '1.0.0', 'vid': 'v_and_no_v', 'exp': 'v1.0.0'},
    # {'ask': '1.0.0', 'vid': 'v_and_no_v', 'exp': 'v1.0.0'},
    {'ask': '1.0.0', 'vid': 'v_and_no_v', 'exp': 'v1.0.0'},
    {'ask': '2.3.7', 'vid': '147', 'exp': '2.3.7'},
    {'ask': 'v2.3.7', 'vid': '147', 'exp': '2.3.7'},
]


@pytest.fixture(scope='module',
                params=test_data,
                ids=['ask=%s,vlist=%s,exp=%s' % (x['ask'], x['vid'], x['exp']) for x in test_data])
def ver_data(request):
    tdata = request.param.copy()
    tdata['vlist'] = content_versions_map[tdata['vid']]
    log.debug('tdata: %s', tdata)
    yield tdata


def test_get_content_version(ver_data):
    log.debug('ver_data: %s', ver_data)
    res = content_version.get_content_version({}, ver_data['ask'], ver_data['vlist'], 'some_content_name')
    log.debug('res: %s', res)
    assert res == ver_data['exp']


latest_test_data = [
    {'vid': '1_0_0_latest', 'exp': '1.0.0'},
    {'vid': 'boring', 'exp': '3.0.0'},
    {'vid': 'no_v', 'exp': '3.0.0'},
]


@pytest.fixture(scope='module',
                params=latest_test_data,
                ids=['vlist=%s,exp=%s' % (x['vid'], x['exp']) for x in latest_test_data])
def latest_ver_data(request):
    tdata = request.param.copy()
    tdata['vlist'] = content_versions_map[tdata['vid']]
    log.debug('tdata: %s', tdata)
    yield tdata


def test_get_latest_version(latest_ver_data):
    log.debug('latest_ver_data: %s', latest_ver_data)
    res = content_version.get_content_version({}, None, latest_ver_data['vlist'], 'some_content_name')
    log.debug('res: %s', res)
    assert res == latest_ver_data['exp']


@pytest.mark.xfail
def test_get_1_0_0_in_content_versions_v_and_no_v():
    ret1 = content_version.get_content_version({}, '1.0.0', content_versions_v_and_no_v, 'some_content_name')
    log.debug('ret1: %s', ret1)
    # assert ret == '1.0.0'

    content_versions_v_and_no_v.reverse()
    ret2 = content_version.get_content_version({}, '1.0.0', content_versions_v_and_no_v, 'some_content_name')
    log.debug('ret2: %s', ret2)
    assert ret1 == ret2


def test_get_latest_in_content_versions_1_0_0_v_and_no_v():
    ret1 = content_version.get_content_version({}, None, content_versions_1_0_v_and_no_v, 'some_content_name')
    log.debug('ret1: %s', ret1)
    # assert ret1 == '3.0.0'
    content_versions_1_0_v_and_no_v.reverse()
    ret2 = content_version.get_content_version({}, None, content_versions_1_0_v_and_no_v, 'some_content_name')
    log.debug('ret2: %s', ret2)
    assert ret1 == ret2


@pytest.mark.xfail
def test_get_latest_in_content_versions_alphanumeric():
    ret = content_version.get_content_version({}, None, content_versions_alphanumeric, 'some_content_name')
    log.debug('ret: %s', ret)
    # is 'a' > '1'?  no idea...
    # assert ret == '3.0.0'


@pytest.mark.xfail
def test_get_latest_in_content_versions_alphanumeric_post():
    ret = content_version.get_content_version({}, None, content_versions_alphanumeric_post, 'some_content_name')
    log.debug('ret: %s', ret)
    assert ret == '0.0.2a'


def test_get_content_version_devel_version_not_in_content_versions():
    # FIXME: use pytest expect_exception stuff
    try:
        ret = content_version.get_content_version({}, 'devel', content_versions_147, 'some_content_name')
        log.debug('ret=%s', ret)
    except exceptions.GalaxyError as e:
        log.exception(e)
        return

    assert False is True, "should have raise an exception earlier"


@pytest.mark.xfail
def test_loose_version_v_and_no_v():
    from distutils.version import LooseVersion
    vers = ['1.0.0', 'v1.0.0']
    loose_versions = [LooseVersion(a) for a in vers]
    log.debug('loose_versions presort: %s', loose_versions)
    loose_versions.sort()
    log.debug('loose_versions sorted: %s', loose_versions)
