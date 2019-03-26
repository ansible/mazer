import pytest


@pytest.fixture
def galaxy_context(tmpdir):
    # tmp_content_path = tempfile.mkdtemp()
    # FIXME: mock
    server = {'url': 'http://localhost:8000',
              'ignore_certs': False}
    content_dir = tmpdir.mkdir('collections')
    collections_dir = content_dir.mkdir('ansible_collections')
    from ansible_galaxy.models.context import GalaxyContext
    return GalaxyContext(server=server, content_path=collections_dir.strpath)
