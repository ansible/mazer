import logging

import pytest

from ansible_galaxy import repository_spec_parse
from ansible_galaxy import exceptions

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


def parse_repository_spec(repository_spec_string, resolver=None):
    result = repository_spec_parse.spec_data_from_string(repository_spec_string,
                                                         resolver=resolver)
    log.debug('result: %s', result)
    return result


def assert_just_keys(parse_result):
    valid_keys = ('name', 'namespace', 'src', 'scm', 'version', 'spec_string', 'fetch_method')

    for key in valid_keys:
        assert key in parse_result, 'expected the results dict to have a "%s" key but it did not' % key

    for result_key in parse_result.keys():
        assert result_key in valid_keys, 'the results had unexpected key="%s"' % result_key


def test_parse_repository_spec_src_no_namespace_required():
    spec_text = 'some_content'
    result = parse_repository_spec(spec_text,
                                   resolver=repository_spec_parse.resolve)

    assert_just_keys(result)
    assert_keys(result, name='some_content', version=None, scm=None, src='some_content')


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
    try:
        parse_repository_spec(spec_text)
    except exceptions.GalaxyClientError:
        return

    assert False, 'spec_text="%s" should have caused a GalaxyClientError' % spec_text
