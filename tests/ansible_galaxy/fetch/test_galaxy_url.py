import logging

import pytest

from ansible_galaxy import exceptions
from ansible_galaxy.fetch import galaxy_url
from ansible_galaxy.models.context import GalaxyContext
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
def galaxy_context_example_invalid(galaxy_context):
    context = GalaxyContext(collections_path=galaxy_context.collections_path,
                            server={'url': 'http://example.invalid',
                                    'ignore_certs': False})
    return context


@pytest.fixture
def galaxy_url_fetch(galaxy_context_example_invalid):
    req_spec = RequirementSpec(namespace='some_namespace',
                               name='some_name',
                               version_spec='==9.3.245')

    galaxy_url_fetch = galaxy_url.GalaxyUrlFetch(requirement_spec=req_spec, galaxy_context=galaxy_context_example_invalid)
    log.debug('galaxy_url_fetch: %s', galaxy_url_fetch)

    return galaxy_url_fetch


def test_galaxy_url_fetch_find(galaxy_url_fetch, requests_mock):
    download_url = 'http://example.invalid/api/v2/collections/some_ns/some_name/versions/9.3.245/artifact'

    requests_mock.get('http://example.invalid/api/',
                      json={'current_version': 'v2'})

    # get CollectionVersionList
    requests_mock.get('http://example.invalid/api/v2/collections/some_ns/some_name/versions/',
                      json={
                          'count': 2,
                          'next': None,
                          'previous': None,
                          'results':
                          [{'version': '1.2.3',
                            'href': 'http://example.invalid/api/v2/collections/some_ns/some_name/versions/1.2.3/'},
                           {'version': '9.3.245',
                            'href': 'http://example.invalid/api/v2/collections/some_ns/some_name/versions/9.3.245/'}]})

    # The request to get the CollectionVersion detail via href from CollectionVersion list
    requests_mock.get('http://example.invalid/api/v2/collections/some_ns/some_name/versions/9.3.245/',
                      json={'download_url': download_url,
                            'metadata': {},
                            'version': '9.3.245'})

    # The Collection detail
    requests_mock.get('http://example.invalid/api/v2/collections/some_namespace/some_name/',
                      json={'versions_url': 'http://example.invalid/api/v2/collections/some_ns/some_name/versions/'})

    res = galaxy_url_fetch.find()

    log.debug('res:%s', res)

    assert res['content']['galaxy_namespace'] == 'some_namespace'
    assert res['content']['repo_name'] == 'some_name'

    assert res['custom']['download_url'] == download_url


def test_galaxy_url_fetch_find_no_repo_data(galaxy_url_fetch, galaxy_context, requests_mock):
    requests_mock.get('http://example.invalid/api/',
                      json={'current_version': 'v2'})
    requests_mock.get('http://example.invalid/api/v2/collections/some_namespace/some_name/',
                      json={})

    # galaxy_url_fetch = galaxy_url.GalaxyUrlFetch(requirement_spec=req_spec, galaxy_context=context)
    # - sorry, some_namespace.some_name (version_spec: ==9.3.245) was not found on http://galaxy.invalid/.
    with pytest.raises(exceptions.GalaxyClientError,
                       match='- sorry, some_namespace.some_name.*version_spec.*was not found on http://example.invalid') as exc_info:
        galaxy_url_fetch.find()

    log.debug('exc_info:%s', exc_info)


def test_galaxy_url_fetch_fetch(galaxy_url_fetch, mocker, requests_mock):
    download_url = 'http://example.invalid/api/v2/collections/some_ns/some_name/versions/9.3.245/artifact'
    collection_path = '/dev/null/path/to/collection.tar.gz'

    mocked_download_fetch_url = mocker.patch('ansible_galaxy.fetch.galaxy_url.download.fetch_url', autospec=True)
    mocked_download_fetch_url.return_value = collection_path

    # download_url = 'http://example.invalid/invalid/whatever'
    find_results = {'content': {'galaxy_namespace': 'some_namespace',
                                'repo_name': 'some_name'},
                    'custom': {'repo_data': {},
                               'download_url': download_url,
                               'repoversion': {'version': '9.3.245'}
                               },
                    }

    res = galaxy_url_fetch.fetch(find_results)

    log.debug('res:%s', res)

    assert isinstance(res, dict)
    assert res['archive_path'] == collection_path
    assert res['custom']['download_url'] == download_url
    assert res['fetch_method'] == 'galaxy_url'
    assert isinstance(res['content'], dict)


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
