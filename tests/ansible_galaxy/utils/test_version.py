import logging

import pytest

from ansible_galaxy.utils.version import normalize_version_string


log = logging.getLogger(__name__)


version_string_to_strip_data = [
    'v1.2.3',
    'V1.2.3',
    'v11.1',

    # TODO: should these be stripped?
    # 'vRfd11',
    # 'v.1'
]

version_string_unmodified_data = [
    '1.2.3',
    'vV11.12',
    'veryBestVersion',
    'v',
    '1.2.4.v1',
    'vAlpha-1.1.2',
    '40.1.0.0.4v2',
    # TODO: should these be stripped?
    'vRfd11',
    'v.1'
]


@pytest.fixture(scope='module',
                params=version_string_to_strip_data)
def version_string_to_strip(request):
    yield request.param


def test_normalize_version_string_to_strip(version_string_to_strip):
    res = normalize_version_string(version_string_to_strip)
    log.debug('res: %s version_string: %s', res, version_string_to_strip)
    assert res != version_string_to_strip
    # assert not res.startswith('v')
    # assert not res.startswith('V')


@pytest.fixture(scope='module',
                params=version_string_unmodified_data)
def version_string_unmodified(request):
    yield request.param


def test_normalize_version_string_unmodified(version_string_unmodified):
    res = normalize_version_string(version_string_unmodified)
    log.debug('res: %s version_string: %s', res, version_string_unmodified)
    assert res == version_string_unmodified
