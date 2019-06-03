import io
import logging
import os

import pytest

from ansible_galaxy import download
from ansible_galaxy import exceptions

log = logging.getLogger(__name__)


def test_fetch_url_404(tmpdir, requests_mock):
    url = 'http://example.invalid/download/some_ns-some_name-1.2.3.tar.gz'

    some_content = b'''<html><head>oopsie</head>\n<body>\nHey, couldn't find that.\n</body>\n'''

    requests_mock.get(url,
                      status_code=404,
                      reason='Not Found',
                      content=some_content)

    with pytest.raises(exceptions.GalaxyDownloadError, match='.*download/some_ns-some_name-1.2.3.tar.gz.*') as exc_info:
        download.fetch_url(url)

    log.debug('exc_info: %s', exc_info)


def test_fetch_bytes_200(requests_mock):
    url = 'http://example.invalid/download/some_ns-some_name-1.2.3.tar.gz'
    some_fd = io.BytesIO(b'Some thing like an error page.\nThis is not a tar file\n\n')

    requests_mock.get(url,
                      status_code=200,
                      reason='OK',
                      body=some_fd,
                      )

    # NOTE: have to pass in chunk_size, just to get requests_mock to work, otherwise
    #       it gets stuck waiting on response.body to closer/eof and gets stuck.
    res = download.fetch_url(url, chunk_size=128)

    log.debug('res: %s', res)
    os.unlink(res)
