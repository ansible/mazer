import pytest

from ansible_galaxy.models.context import GalaxyContext


@pytest.fixture
def galaxy_context(tmpdir):
    # tmp_content_path = tempfile.mkdtemp()
    # FIXME: mock
    server = {'url': 'http://localhost:8000',
              'ignore_certs': False}
    content = tmpdir.mkdir('content')
    return GalaxyContext(server=server, content_path=content.strpath)
