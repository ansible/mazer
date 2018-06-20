import logging
import pytest

from ansible_galaxy.fetch import galaxy_url

log = logging.getLogger(__name__)

EXAMPLE_REPO_VERSION_LATEST = \
        {
            "id": 55616,
            "version": "1.1.0",
            "tag": "1.1.0",
            "commit_date": "2015-11-24T13:00:32-05:00",
            "commit_sha": None,
            "download_url": "https://github.com/atestuseraccount/ansible-role-logstash/archive/1.1.0.tar.gz",
            "url": "",
            "related": {},
            "summary_fields": {},
            "created": "2018-05-18T13:13:40.208012Z",
            "modified": "2018-05-18T13:13:40.208037Z",
            "active": None
        }

EXAMPLE_REPO_VERSIONS_LIST = \
    [
        {
            "id": 55617,
            "version": "1.0.6",
            "tag": "1.0.6",
            "commit_date": "2015-11-16T11:08:07-05:00",
            "commit_sha": None,
            "download_url": "https://github.com/atestuseraccount/ansible-role-logstash/archive/1.0.6.tar.gz",
            "url": "",
            "related": {},
            "summary_fields": {},
            "created": "2018-05-18T13:13:40.344064Z",
            "modified": "2018-05-18T13:13:40.344088Z",
            "active": None
        },
        EXAMPLE_REPO_VERSION_LATEST,
    ]


# Note that select_repository_version just gets the full version object
# from repoversions. It does not sort or compare versions aside from equality
@pytest.mark.parametrize("repoversions,version,expected", [
    ([], None, {}),
    ([{'version': '1.2.3'}],
     '1.2.3',
     {'version': '1.2.3'}),
    # the version requested isnt in repoversions, exp a {} result
    ([{'version': '1.2.4'}],
     '1.2.3',
     {}),
    # repoversions has 1.2.3 so expect the full repoversion object returned
    ([{'version': '1.2.2'},
      {'version': '1.2.3'},
      {'version': '1.2.4'},
      ],
     '1.2.3',
     {'version': '1.2.3'}),
    ([{'version': '1.2.2'},
      {'version': '1.2.3'},
      {'version': '1.2.4'},
      ],
     '1.2.4',
     {'version': '1.2.4'}),
    # an example with full repo_version objects
    (EXAMPLE_REPO_VERSIONS_LIST,
     '1.1.0',
     EXAMPLE_REPO_VERSION_LATEST),
    # if repoversions somehow ends up with two repo_version objects with same version
    ([{'version': '1.2.2',
       'url': 'http://thefirsturl.example.com'},
      {'version': '1.2.2',
       'url': 'http://thesecondurl.example.com'},
      ],
     '1.2.2',
     {'version': '1.2.2',
      'url': 'http://thesecondurl.example.com'}),
])
def test_select_repository_versions(repoversions, version, expected):
    log.debug('repoversions: %s', repoversions)
    log.debug('version: %s', version)
    log.debug('expected: %s', expected)
    res = galaxy_url.select_repository_version(repoversions, version)

    assert isinstance(res, dict)

    if res and expected:
        assert res['version'] == expected['version']

    assert res == expected


# see https://github.com/ansible/mazer/issues/79
def test_select_repository_version_empty_repoversions():
    repoversions = []
    version = '1.2.3'

    res = galaxy_url.select_repository_version(repoversions, version)

    assert isinstance(res, dict)
    assert res == {}
