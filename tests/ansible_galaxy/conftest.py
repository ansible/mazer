import pytest


@pytest.fixture
def galaxy_context(tmpdir):
    # FIXME: mock
    server = {'url': 'http://localhost:8000',
              'ignore_certs': False}
    collections_path = tmpdir.mkdir('collections')

    from ansible_galaxy.models.context import GalaxyContext

    return GalaxyContext(server=server, collections_path=collections_path.strpath)
