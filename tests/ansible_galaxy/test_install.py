
import logging
import pprint

import pytest

from ansible_galaxy import exceptions
from ansible_galaxy import install
from ansible_galaxy.models.repository_spec import RepositorySpec

log = logging.getLogger(__name__)
pf = pprint.pformat


def display_callback(msg, **kwargs):
    log.debug(msg)


def test_find(mocker):
    mock_fetcher = mocker.MagicMock(name='MockFetch')
    mock_fetcher.find.return_value = {}

    res = install.find(mock_fetcher)

    log.debug('res: %s', res)

    assert res == {}


def test_fetch(mocker):
    mock_fetcher = mocker.MagicMock(name='MockFetch')
    mock_fetcher.fetch.return_value = {}
    repo_spec = RepositorySpec(namespace='some_namespace',
                               name='some_name',
                               version='86.75.30')
    find_results = {}

    res = install.fetch(mock_fetcher, repo_spec, find_results)

    log.debug('res: %s', res)


def test_fetch_download_error(mocker):
    mock_fetcher = mocker.MagicMock(name='MockFetch')
    mock_fetcher.fetch.side_effect = exceptions.GalaxyDownloadError(url='http://example.invalid')

    repo_spec = RepositorySpec(namespace='some_namespace',
                               name='some_name',
                               version='86.75.30')
    find_results = {}

    with pytest.raises(exceptions.GalaxyDownloadError) as exc_info:
        install.fetch(mock_fetcher, repo_spec, find_results)
    log.debug("exc_info: %s", exc_info)
