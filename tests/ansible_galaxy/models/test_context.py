
import logging

import six

from ansible_galaxy.models import context

log = logging.getLogger(__name__)


class FauxOptions(object):
    default_data = {}

    def __init__(self, option_data=None):
        option_data = option_data or {}
        self._data = self.default_data.copy()
        # add in passed in options
        self._data.update(option_data)

    def __getattr__(self, attr):
        try:
            return self._data[attr]
        except KeyError:
            raise AttributeError('FauxOptions has no "%s" attr' % attr)

    def __repr__(self):
        return '%s(option_data=%s)' % (self.__class__.__name__,
                                       self._data)


# Default Faux... get it?
# a FauxOption with defaults for some of the options, equiv to
# default=None, in the optparse add_option args
class DefauxOptions(FauxOptions):
    default_data = {'content_path': None,
                    'server_url': None,
                    'ignore_certs': None}


def assert_types(galaxy_context):
    assert isinstance(galaxy_context.roles_paths, list)
    assert isinstance(galaxy_context.content, dict)


def test_context_from_config_and_options_none_options():
    options = None
    galaxy_context = context.GalaxyContext.from_config_and_options(config={},
                                                                   options=options)

    # assert_types(galaxy_context)
    # assert galaxy_context.options is not None
    assert galaxy_context.servers is not None
    assert galaxy_context.content_roots is not None
    assert isinstance(galaxy_context.servers, list)
    assert isinstance(galaxy_context.content_roots, list)
    # assert galaxy_context.roles_paths == []

    # TODO/FIXME: what should DATA_PATH be for tests? currently based on __file__ which seems wrong
    # assert galaxy_context.DATA_PATH


# FIXME: paramerize options with pytest fixture
def test_context_from_config_and_options_options_server_url():
    # roles_path = ['/dev/null/doesntexist']
    # role_type = 'module'
    server_url = 'http://example.com:9999/'
    ignore_certs = False

    options = DefauxOptions(option_data={'server_url': server_url,
                                         'ignore_certs': ignore_certs})

    galaxy_context = context.GalaxyContext.from_config_and_options(config={},
                                                                   options=options)

    assert isinstance(galaxy_context.servers, list)

    log.debug('servers: %s', galaxy_context.servers)

    assert galaxy_context.servers[0]['url'] == server_url
    assert galaxy_context.servers[0]['ignore_certs'] == ignore_certs

    assert len(galaxy_context.servers) == 1


def test_context_with_options_content_path():
    content_path = '/dev/null/some_content_path'

    options = DefauxOptions(option_data={'content_path': content_path})

    galaxy_context = context.GalaxyContext.from_config_and_options(config={},
                                                                   options=options)

    assert isinstance(galaxy_context.content_roots, list)

    log.debug('content_roots: %s', galaxy_context.content_roots)

    assert len(galaxy_context.content_roots) == 1

    assert galaxy_context.content_roots[0] == content_path


def test_context_with_options_content_path_and_server_url_and_servers():
    content_path = '/dev/null/some_content_path'
    server_url = 'http://example.com:9999/'
    ignore_certs = False

    options = DefauxOptions(option_data={'content_path': content_path,
                                         'server_url': server_url,
                                         'ignore_certs': ignore_certs})

    test_servers = [
        {'url': 'http://test1.example.com:9999/',
         'ignore_certs': False},
        {'url': 'http://test2.example.com:9999/',
         'ignore_certs': True},
    ]

    test_content_roots = ['/dev/null/some_test_content_path_1',
                          '/dev/null/some_test_content_path_2',
                          ]

    config = {'servers': test_servers,
              'content_roots': test_content_roots}
    galaxy_context = context.GalaxyContext.from_config_and_options(config=config,
                                                                   options=options)

    log.debug('content_roots: %s', galaxy_context.content_roots)
    assert isinstance(galaxy_context.content_roots, list)

    import json
    log.debug('servers: %s', json.dumps(galaxy_context.servers, indent=4))

    assert isinstance(galaxy_context.servers, list)

    log.debug('test_servers: %s', json.dumps(test_servers, indent=4))

    assert len(galaxy_context.content_roots) == 3
    assert len(galaxy_context.servers) == 3

    assert galaxy_context.content_roots[0] == content_path

    assert galaxy_context.content_roots[1] == \
        test_content_roots[0]

    assert galaxy_context.servers[0]['url'] == server_url
    assert galaxy_context.servers[0]['ignore_certs'] == ignore_certs

    assert galaxy_context.servers[1]['url'] == \
        test_servers[0]['url']
    assert galaxy_context.servers[1]['ignore_certs'] == ignore_certs

    assert galaxy_context.servers[2]['url'] == \
        test_servers[1]['url']

    # test_servers[2] has ignore_certs = True, verify it stays
    assert galaxy_context.servers[2]['ignore_certs'] is True


def test_context_from_config_and_options_none_config():
    options = DefauxOptions()

    config_obj = None

    exception = False
    try:
        context.GalaxyContext.from_config_and_options(config_obj, options)
    except AttributeError:
        exception = True
        return

    assert exception, 'config was None, an AttributeError should have been raise but it was not raise'


def test_context_from_config_and_options():
    content_path = '/dev/null/some_content_path'
    server_url = 'http://example.com:9999/'
    ignore_certs = False

    options = DefauxOptions(option_data={'content_path': content_path,
                                         'server_url': server_url,
                                         'ignore_certs': ignore_certs})

    test_servers = [
        {'url': 'http://test1.example.com:9999/',
         'ignore_certs': False},
        {'url': 'http://test2.example.com:9999/',
         'ignore_certs': True},
    ]

    test_content_roots = [
         '/dev/null/some_test_content_path_1',
         '/dev/null/some_test_content_path_2',
    ]

    config_obj = {'servers': test_servers,
                  'content_roots': test_content_roots}

    galaxy_context = context.GalaxyContext.from_config_and_options(config_obj, options)

    log.debug('galaxy_context: %s', galaxy_context)
    assert isinstance(galaxy_context, context.GalaxyContext)

    assert galaxy_context.server_url == server_url
    assert isinstance(galaxy_context.content_roots, list)
    assert isinstance(galaxy_context.servers, list)
    assert len(galaxy_context.content_roots) == 3
    assert len(galaxy_context.servers) == 3
    assert galaxy_context.content_roots[0] == content_path
    assert galaxy_context.servers[0]['url'] == server_url
    assert galaxy_context.servers[0]['ignore_certs'] == ignore_certs


def test_context_repr():
    content_path = '/dev/null/some_content_path'
    server_url = 'http://example.com:9999/'
    ignore_certs = False
    verbosity = 4
    some_option = 'AGAGAGAGAG'

    options = DefauxOptions(option_data={'content_path': content_path,
                                         'server_url': server_url,
                                         'ignore_certs': ignore_certs,
                                         'verbosity': verbosity,
                                         'some_option': some_option})

    config = {'servers': [],
              'content_roots': []}

    galaxy_context = context.GalaxyContext.from_config_and_options(config=config,
                                                                   options=options)

    rep_res = repr(galaxy_context)

    log.debug('rep_res: %s', rep_res)

    assert isinstance(rep_res, six.text_type)
    assert 'content_roots' in rep_res
    assert 'servers' in rep_res
    assert 'some_content_path' in rep_res


def test_context_properties():
    content_path = '/dev/null/some_content_path'
    server_url = 'http://example.com:9999/'
    ignore_certs = False

    options = DefauxOptions(option_data={'content_path': content_path,
                                         'server_url': server_url,
                                         'ignore_certs': ignore_certs})

    galaxy_context = context.GalaxyContext.from_config_and_options(config={},
                                                                   options=options)

    assert galaxy_context.server_url == server_url
    assert galaxy_context.ignore_certs == ignore_certs
    assert galaxy_context.content_path == content_path


def test_context_properties_no_servers_no_server_url():

    galaxy_context = context.GalaxyContext(servers=[],
                                           content_roots=[])

    assert galaxy_context.server_url is None
    assert galaxy_context.ignore_certs is None
    assert galaxy_context.content_path is None
