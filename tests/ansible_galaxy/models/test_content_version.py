
import logging


from ansible_galaxy.models import content_version
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


def test_get_content_version_prod_version_in_content_versions():
    ret = content_version.get_content_version({}, 'prod', content_versions_147, None)
    log.debug('ret=%s', ret)

    assert ret == 'prod'


content_versions_147 = [
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
    {
        "id": 128,
        "name": "prod",
        "release_date": "2018-05-01T11:54:19-04:00",
        "url": "",
        "related": {},
        "summary_fields": {},
        "created": "2018-05-01T16:11:42.114698Z",
        "modified": "2018-05-01T16:11:42.427811Z",
        "active": True
    }
]


def test_get_content_version_devel_version_not_in_content_versions():
    # FIXME: use pytest expect_exception stuff
    try:
        ret = content_version.get_content_version({}, 'devel', content_versions_147, 'some_content_name')
        log.debug('ret=%s', ret)
    except exceptions.GalaxyError as e:
        log.exception(e)
        return

    assert False is True, "should have raise an exception earlier"


def test_get_content_version_2_3_7_version_in_content_versions():
    # FIXME: use pytest expect_exception stuff
    ret = content_version.get_content_version({}, '2.3.7', content_versions_147, 'some_content_name')
    log.debug('ret=%s', ret)
    assert ret == '2.3.7'
