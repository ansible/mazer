import logging

import pytest

from ansible_galaxy import exceptions
from ansible_galaxy.fetch import galaxy_url
from ansible_galaxy.models.requirement_spec import RequirementSpec

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


@pytest.fixture
def galaxy_url_fetch(galaxy_context):
    req_spec = RequirementSpec(namespace='some_namespace',
                               name='some_name',
                               version_spec='==9.3.245')

    galaxy_url_fetch = galaxy_url.GalaxyUrlFetch(requirement_spec=req_spec, galaxy_context=galaxy_context)
    log.debug('galaxy_url_fetch: %s', galaxy_url_fetch)

    return galaxy_url_fetch


def test_galaxy_url_fetch_find(galaxy_url_fetch, mocker):
    MockedGalaxyAPI = mocker.patch('ansible_galaxy.fetch.galaxy_url.GalaxyAPI', autospec=True)

    external_url = 'http://example.invalid/invalid/whatever'

    instance = MockedGalaxyAPI.return_value
    instance.lookup_repo_by_name.return_value = {'related': {'versions': 'http://example.invalid/foo'},
                                                 'external_url': external_url}
    instance.fetch_content_related.return_value = [{'version': '1.2.3'}, {'version': '9.3.245'}]

    res = galaxy_url_fetch.find()

    log.debug('res:%s', res)

    assert res['content']['galaxy_namespace'] == 'some_namespace'
    assert res['content']['repo_name'] == 'some_name'

    assert res['custom']['external_url'] == external_url


def test_galaxy_url_fetch_find_no_repo_data(galaxy_url_fetch, mocker):
    MockedGalaxyAPI = mocker.patch('ansible_galaxy.fetch.galaxy_url.GalaxyAPI', autospec=True)

    instance = MockedGalaxyAPI.return_value
    instance.lookup_repo_by_name.return_value = {}

    faux_server_url = 'http://galaxy.invalid/'
    instance.api_server = faux_server_url

    with pytest.raises(exceptions.GalaxyClientError, match='- sorry, some_namespace.some_name was not found on %s' % faux_server_url) as exc_info:
        galaxy_url_fetch.find()

    log.debug('exc_info:%s', exc_info)


def test_galaxy_url_fetch_fetch(galaxy_url_fetch, mocker):
    collection_path = '/dev/null/path/to/collection.tar.gz'

    mocked_download_fetch_url = mocker.patch('ansible_galaxy.fetch.galaxy_url.download.fetch_url', autospec=True)
    mocked_download_fetch_url.return_value = collection_path

    find_results = {'content': {'galaxy_namespace': 'some_namespace',
                                'repo_name': 'some_name'},
                    'custom': {'repo_data': {},
                               'external_url': 'http://example.invalid/invalid/whatever',
                               'repoversion': {'version': '9.3.245'}
                               },
                    }

    res = galaxy_url_fetch.fetch(find_results)

    log.debug('res:%s', res)

    assert isinstance(res, dict)
    assert res['archive_path'] == collection_path
    assert res['download_url'] == 'http://example.invalid/invalid/whatever/archive/9.3.245.tar.gz'
    assert res['fetch_method'] == 'galaxy_url'
    assert isinstance(res['content'], dict)
    assert res['content']['fetched_version'] == '9.3.245'


# Note that select_collection_version just gets the full version object
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
def test_select_collection_version(repoversions, version, expected):
    log.debug('repoversions: %s', repoversions)
    log.debug('version: %s', version)
    log.debug('expected: %s', expected)
    res = galaxy_url.select_repository_version(repoversions, version)

    assert isinstance(res, dict)

    if res and expected:
        assert res['version'] == expected['version']

    assert res == expected


# see https://github.com/ansible/mazer/issues/79
def test_select_collection_version_empty_repoversions():
    repoversions = []
    version = '1.2.3'

    res = galaxy_url.select_repository_version(repoversions, version)

    assert isinstance(res, dict)
    assert res == {}


# def test_get_download_url_no_data():
#    res = galaxy_url.get_download_url()

#    log.debug('res: %s', res)


def test_get_download_url_empty_data():
    repo_data = {}
    external_url = ""
    repoversion = []
    res = galaxy_url.get_download_url(repo_data=repo_data, external_url=external_url, repoversion=repoversion)

    log.debug('res: %s', res)
    assert res is None


def test_get_download_url_download_url_in_repo_data():
    download_url = 'https://github.com/alikins/collection_reqs_test/archive/0.0.13.tar.gz'
    repo_data = {'download_url': download_url}
    external_url = 'https://github.com/alikins/collection_reqs_test'
    repoversion = []
    res = galaxy_url.get_download_url(repo_data=repo_data, external_url=external_url, repoversion=repoversion)

    log.debug('res: %s', res)
    assert res == download_url


def test_get_download_url_download_url_in_repo_version():
    repo_data = {}
    external_url = 'https://github.com/alikins/collection_reqs_test'
    repoversion = EXAMPLE_REPO_VERSIONS_LIST[0]
    res = galaxy_url.get_download_url(repo_data=repo_data, external_url=external_url, repoversion=repoversion)

    log.debug('res: %s', res)
    assert res == EXAMPLE_REPO_VERSIONS_LIST[0]['download_url']


def test_get_download_url_no_download_url_in_repodata_or_repoversion():
    repo_data = {}
    external_url = 'https://github.com/alikins/collection_reqs_test'
    repoversion = EXAMPLE_REPO_VERSIONS_LIST[0].copy()
    del repoversion['download_url']

    res = galaxy_url.get_download_url(repo_data=repo_data, external_url=external_url, repoversion=repoversion)

    log.debug('res: %s', res)
    assert res == 'https://github.com/alikins/collection_reqs_test/archive/1.0.6.tar.gz'
