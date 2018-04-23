
import logging

from ansible_galaxy.models import context

log = logging.getLogger(__name__)


class FauxOptions(object):
    def __init__(self, option_data=None):
        self._data = option_data or {}

    def __getattr__(self, attr):
        try:
            return self._data[attr]
        except KeyError:
            raise AttributeError('FauxOptions has no "%s" attr' % attr)


def assert_types(galaxy_context):
    assert isinstance(galaxy_context.roles_paths, list)
    assert isinstance(galaxy_context.content, dict)


def test_context():
    options = None
    galaxy_context = context.GalaxyContext(options=options)

    assert_types(galaxy_context)
    assert galaxy_context.roles_paths == []

    # TODO/FIXME: what should DATA_PATH be for tests? currently based on __file__ which seems wrong
    # assert galaxy_context.DATA_PATH

    assert galaxy_context.options == options


# FIXME: paramerize options with pytest fixture
def test_context_with_options():
    roles_path = ['/dev/null/doesntexist']
    role_type = 'module'
    options = FauxOptions(option_data={'roles_path': roles_path,
                                       'role_type': role_type})
    galaxy_context = context.GalaxyContext(options=options)

    assert_types(galaxy_context)
    assert galaxy_context.roles_paths == roles_path
    assert galaxy_context.content == {}
    assert galaxy_context.roles == {}
    assert galaxy_context.options == options
