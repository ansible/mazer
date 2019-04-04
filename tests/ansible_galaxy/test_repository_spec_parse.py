import logging
import os

import pytest

from ansible_galaxy import repository_spec_parse
from ansible_galaxy import exceptions
from ansible_galaxy.models.repository_spec import FetchMethods

log = logging.getLogger(__name__)


split_kwarg_valid_test_cases = \
    ['something',
     '1.2.3',
     'version=1.2.3',
     'name=somename',

     # weird but valid
     'name==',
     'name=name',
     'name=version',
     'name=war=peace',

     ]


@pytest.fixture(scope='module',
                params=split_kwarg_valid_test_cases)
def split_kwarg_valid(request):
    yield request.param


def test_split_kwarg_valid(split_kwarg_valid):
    valid_keywords = ('name', 'version')
    result = repository_spec_parse.split_kwarg(split_kwarg_valid, valid_keywords)
    log.debug('spec=%s result=%s', split_kwarg_valid, [x for x in result])


split_kwarg_invalid_test_cases = \
    ['=',
     'some_invalid_keyword=foo',
     'blip=',
     ]


@pytest.fixture(scope='module',
                params=split_kwarg_invalid_test_cases)
def split_kwarg_invalid(request):
    yield request.param


def test_split_kwarg_invalid(split_kwarg_invalid):
    valid_keywords = ('name', 'version')
    try:
        repository_spec_parse.split_kwarg(split_kwarg_invalid, valid_keywords)
    except exceptions.GalaxyClientError as e:
        log.exception(e)
        return

    assert False, 'Expected to get a GalaxyClientError for invalid kwargs for %s' % split_kwarg_invalid


split_comma_test_cases = \
    ['foo',
     'foo,1.2.3',
     'foo,version=1.2.3',
     'foo,1.2.3,somename',
     'foo,1.2.3,name=somename',
     'foo,1.2.3,somename,somescm',
     'foo,1.2.3,somename,somescm,someextra'
     ]


@pytest.fixture(scope='module',
                params=split_comma_test_cases)
def split_comma(request):
    yield request.param


def test_split_comma(split_comma):
    valid_keywords = ('name', 'version')
    result = repository_spec_parse.split_comma(split_comma, valid_keywords)
    log.debug('spec=%s result=%s', split_comma, [x for x in result])


just_src = {'src': 'something'}
src_ver = {'src': 'something',
           'version': '1.2.3'}
src_name = {'src': 'something',
            'name': 'somename'}
full_info = {'src': 'something',
             'version': '1.2.3',
             'name': 'somename'}
split_repository_spec_test_cases = \
    [('something', just_src),
     ('something,1.2.3', src_ver),
     ('something,version=1.2.3', src_ver),
     ('something,1.2.3,somename', full_info),
     ('something,1.2.3,name=somename', full_info),
     ('something,name=somename,version=1.2.3', full_info),
     ('something,1.2.3,somename', full_info),
     # dont want to expect this to work
     # ('something,name=somename,1.2.3', full_info),
     ]


@pytest.fixture(scope='module',
                params=split_repository_spec_test_cases,
                ids=[x[0] for x in split_repository_spec_test_cases])
def split_repository_spec_fixture(request):
    yield request.param


def test_split_repository_spec(split_repository_spec_fixture):
    valid_keywords = ('src', 'version', 'name', 'scm')
    result = repository_spec_parse.split_repository_spec(split_repository_spec_fixture[0], valid_keywords)
    log.debug('spec=%s result=%s', split_repository_spec_fixture[0], result)
    assert result == split_repository_spec_fixture[1]


def assert_keys(repository_spec, name=None, version=None,
                scm=None, src=None, namespace=None):
    # name = name or ''
    # src = src or ''
    assert isinstance(repository_spec, dict)

    log.debug('repository_spec: %s', repository_spec)
    # TODO: should it default to empty string?
    assert repository_spec['name'] == name, \
        'repository_spec name=%s does not match expected name=%s' % (repository_spec['name'], name)
    assert repository_spec['version'] == version
    assert repository_spec['scm'] == scm
    assert repository_spec['src'] == src, \
        'repository_spec src=%s does not match expected src=%s' % (repository_spec['src'], src)


def parse_repository_spec(repository_spec_string):
    result = repository_spec_parse.spec_data_from_string(repository_spec_string)
    log.debug('result: %s', result)
    return result


def assert_just_keys(parse_result):
    valid_keys = ('name', 'namespace', 'src', 'scm', 'version', 'spec_string', 'fetch_method')

    for key in valid_keys:
        assert key in parse_result, 'expected the results dict to have a "%s" key but it did not' % key

    for result_key in parse_result.keys():
        assert result_key in valid_keys, 'the results had unexpected key="%s"' % result_key


def test_parse_repository_spec_src():
    spec_text = 'some_namespace.some_content'
    result = parse_repository_spec(spec_text)

    assert_just_keys(result)
    assert_keys(result, namespace='some_namespace', name='some_content',
                version=None, scm=None, src='some_namespace.some_content')


def test_parse_repository_spec_src_version():
    spec_text = 'some_namespace.some_content,1.0.0'
    result = parse_repository_spec(spec_text)

    assert_just_keys(result)
    assert_keys(result, namespace='some_namespace', name='some_content',
                version='1.0.0', scm=None, src='some_namespace.some_content')


def test_parse_repository_spec_src_version_name():
    spec_text = 'some_namespace.some_content,1.2.3,somename'
    result = parse_repository_spec(spec_text)

    assert_just_keys(result)
    assert_keys(result, namespace='some_namespace', name='somename',
                version='1.2.3', scm=None, src='some_namespace.some_content')


def test_parse_repository_spec_src_key_value():
    spec_text = 'src=some_namespace.some_content'
    result = parse_repository_spec(spec_text)

    assert_just_keys(result)
    assert_keys(result, namespace='some_namespace', name='some_content',
                version=None, scm=None, src='some_namespace.some_content')


def test_parse_repository_spec_src_version_key_value():
    spec_text = 'some_namespace.some_content,version=1.0.0'
    result = parse_repository_spec(spec_text)

    assert_just_keys(result)
    assert_keys(result, namespace='some_namespace', name='some_content',
                version='1.0.0', scm=None, src='some_namespace.some_content')


def test_parse_repository_spec_src_version_name_key_value():
    spec_text = 'some_namespace.some_content,1.2.3,name=somename'
    result = parse_repository_spec(spec_text)

    assert_just_keys(result)
    assert_keys(result, namespace='some_namespace', name='somename',
                version='1.2.3', scm=None, src='some_namespace.some_content')


def test_parse_repository_spec_src_version_name_something_invalid_key_value():
    spec_text = 'some_content,1.0.0,name=some_name,foo=bar,some_garbage'
    match_re = '.*%s.*' % spec_text
    with pytest.raises(exceptions.GalaxyError, match=match_re):
        parse_repository_spec(spec_text)


# For the cases where getting real repo_spec data means having an artifact and splitting it open, easier to
# test some variants just for choose_fetch_method
choose_fetch_method_cases = \
    [
        {'spec': 'geerlingguy.apache',
         'expected': FetchMethods.GALAXY_URL},
        {'spec': 'geerlingguy.apache,2.1.1',
         'expected': FetchMethods.GALAXY_URL},
        {'spec': 'testing.ansible-testing-content',
         'expected': FetchMethods.GALAXY_URL},
        {'spec': 'testing.ansible-testing-content,1.2.3,name=testing-content',
         'expected': FetchMethods.GALAXY_URL},
        {'spec': 'testing.ansible-testing-content,1.2.3,also-testing-content,stuff',
         'expected': FetchMethods.GALAXY_URL},
        {'spec': 'git+https://github.com/geerlingguy/ansible-role-apache.git,version=2.0.0',
         'expected': FetchMethods.SCM_URL},
        {'spec': 'git+https://mazertestuser@github.com/geerlingguy/ansible-role-apache.git,version=2.0.0',
         'expected': FetchMethods.SCM_URL},

        # This is odd, use the source LICENSE in mazer as an example file name instead of mocking os.path.isfile()
        {'spec': '%s,name=the_license' % os.path.normpath(os.path.join(os.path.dirname(__file__), '../../LICENSE')),
         'expected': FetchMethods.LOCAL_FILE},
        {'spec': 'https://someserver.example.com/collections/some_ns-some_name-1.2.3.tar.gz',
         'expected': FetchMethods.REMOTE_URL},
        {'spec': 'https://docs.ansible.com,name=the_docs',
         'expected': FetchMethods.REMOTE_URL},
    ]


@pytest.fixture(scope='module',
                params=choose_fetch_method_cases,
                ids=[x['spec'] for x in choose_fetch_method_cases])
def choose_fetch_method_case(request):
    yield request.param


def test_choose_fetch_method_urls(choose_fetch_method_case):
    log.debug('spec=%s expected=%s', choose_fetch_method_case['spec'], choose_fetch_method_case['expected'])
    res = repository_spec_parse.choose_repository_fetch_method(choose_fetch_method_case['spec'])

    log.debug('spec=%s expected=%s result=%s', choose_fetch_method_case['spec'], choose_fetch_method_case['expected'], res)
    assert res == choose_fetch_method_case['expected']


choose_fetch_method_invalid_cases = \
    [
        {'spec': 'foo'},
        {'spec': 'foo,1.2.3'},
        {'spec': 'notarealscheme://blippy.foo'},
        {'spec': 'ldap://somehost.example.com'},
    ]


@pytest.fixture(scope='module',
                params=choose_fetch_method_invalid_cases,
                ids=[x['spec'] for x in choose_fetch_method_invalid_cases])
def choose_fetch_method_invalid_case(request):
    yield request.param


def test_choose_fetch_method_invalid(choose_fetch_method_invalid_case):
    log.debug('spec=%s', choose_fetch_method_invalid_case['spec'])
    with pytest.raises(exceptions.GalaxyError):
        res = repository_spec_parse.choose_repository_fetch_method(choose_fetch_method_invalid_case['spec'])
        log.debug('res: %s', res)
