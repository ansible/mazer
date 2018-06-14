import logging

from ansible_galaxy import exceptions
from ansible_galaxy.models.content import VALID_ROLE_SPEC_KEYS
from ansible_galaxy.utils import yaml_parse
from ansible_galaxy import content_spec_parse
from ansible_galaxy import galaxy_content_spec


log = logging.getLogger(__name__)


def parse_spec(content_spec, resolver=None):
    result = yaml_parse.yaml_parse(content_spec, resolver=resolver)
    log.debug('result=%s', result)
    return result


def assert_keys(content_spec, name=None, version=None,
                scm=None, src=None, namespace=None):
    # name = name or ''
    # src = src or ''
    assert isinstance(content_spec, dict)

    log.debug('content_spec: %s', content_spec)
    # TODO: should it default to empty string?
    assert content_spec['name'] == name, \
        'content_spec name=%s does not match expected name=%s' % (content_spec['name'], name)
    assert content_spec.get('namespace') == namespace
    assert content_spec['version'] == version
    assert content_spec['scm'] == scm
    assert content_spec['src'] == src, \
        'content_spec src=%s does not match expected src=%s' % (content_spec['src'], src)


def test_yaml_parse_empty_string_no_namespace_required():
    spec = ''
    result = parse_spec(spec, resolver=content_spec_parse.resolve)

    assert_keys(result, name='', version=None, scm=None, src='')


def test_yaml_parse_empty_string():
    spec = ''
    try:
        parse_spec(spec)
    except exceptions.GalaxyError as e:
        log.exception(e)
        return

    assert False, 'Expected a GalaxyError here because the content_spec didnt have a namespace'


def test_yaml_parse_just_name():
    spec = 'some_namespace.some_content'
    result = parse_spec(spec)

    assert_keys(result, namespace='some_namespace', name='some_content',
                version=None, scm=None, src='some_namespace.some_content')


def test_yaml_parse_just_name_no_namespace_required():
    spec = 'some_content'
    result = parse_spec(spec, resolver=content_spec_parse.resolve)

    assert_keys(result, name='some_content', version=None, scm=None, src='some_content')


def test_yaml_parse_name_and_version():
    spec = 'some_namespace.some_content,1.0.0'
    result = parse_spec(spec)

    assert_keys(result, namespace='some_namespace', name='some_content',
                version='1.0.0', scm=None, src='some_namespace.some_content')


def test_yaml_parse_name_and_version_key_value():
    spec = 'some_namespace.some_content,version=1.0.0'
    result = parse_spec(spec)

    assert_keys(result, namespace='some_namespace', name='some_content',
                version='1.0.0', scm=None, src='some_namespace.some_content')


def test_yaml_parse_name_github_url():
    spec = 'git+https://github.com/geerlingguy/ansible-role-awx.git,1.0.0'
    result = parse_spec(spec)

    assert_keys(result, name='ansible-role-awx', version='1.0.0', scm='git', src='https://github.com/geerlingguy/ansible-role-awx.git')


def test_yaml_parse_name_github_url_keyword_version():
    spec = 'git+https://github.com/geerlingguy/ansible-role-awx.git,version=1.0.0'
    result = parse_spec(spec)

    assert_keys(result, name='ansible-role-awx', version='1.0.0', scm='git', src='https://github.com/geerlingguy/ansible-role-awx.git')


def test_yaml_parse_name_non_github_url():
    buf = 'git+https://git.example.com/geerlingguy/ansible-role-awx.git,1.0.0'
    result = parse_spec(buf)

    assert_keys(result, name='ansible-role-awx', version='1.0.0', scm='git', src='https://git.example.com/geerlingguy/ansible-role-awx.git')


# See https://github.com/ansible/galaxy-cli/wiki/Content-Versioning#versions-in-galaxy-cli
#
# "When providing a version, provide the semantic version with or without the leading 'v' or 'V'."
#
def test_yaml_parse_name_and_version_leading_V():
    spec = 'some_namespace.some_content,V1.0.0'
    result = parse_spec(spec)

    assert_keys(result, namespace='some_namespace', name='some_content',
                version='V1.0.0', scm=None, src='some_namespace.some_content')


def test_yaml_parse_name_and_version_leading_v():
    spec = 'some_namespace.some_content,v1.0.0'
    result = parse_spec(spec)

    assert_keys(result, namespace='some_namespace', name='some_content',
                version='v1.0.0', scm=None, src='some_namespace.some_content')


def test_yaml_parse_name_and_version_leading_v_no_namespace_required():
    spec = 'some_content,v1.0.0'
    result = parse_spec(spec, resolver=content_spec_parse.resolve)

    assert_keys(result, name='some_content',
                version='v1.0.0', scm=None, src='some_content')


# proving a name and a version as comma separated key values
def test_yaml_parse_name_with_name_key_value():
    spec = 'some_content,name=other_name'
    result = parse_spec(spec, resolver=content_spec_parse.resolve)

    # TODO: what should 'src' be for this cases?
    assert_keys(result, name='other_name', version=None, scm=None, src='some_content')


# def test_yaml_parse_a_list_of_strings():
#    spec = ['some_content', 'something_else']
#    parse_spec(spec)

    # TODO: verify we get the right exception


def test_yaml_parse_an_empty_dict():
    spec = {}
    result = parse_spec(spec)

    assert_keys(result, name=None, version=None, scm=None, src=None)


def test_yaml_parse_a_dict():
    spec = {'name': 'some_name',
            'version': '1.2.4',
            'src': 'galaxy.role'}
    result = parse_spec(spec)

    assert_keys(result, namespace='galaxy', name='some_name',
                version='1.2.4', scm=None, src='galaxy.role')


def test_yaml_parse_a_dict_with_extra_invalid_keys():
    spec = {'name': 'some_name',
            'version': '1.2.4',
            'src': 'galaxy.role',
            'favorite_tea': 'sweet',
            'module': 'some_module',
            'url': 'http://example.com/galaxy/foo'}
    result = parse_spec(spec)

    assert_keys(result, namespace='galaxy', name='some_name',
                version='1.2.4', scm=None, src='galaxy.role')
    result_keys = set(result.keys())
    valid_keys = set(VALID_ROLE_SPEC_KEYS)
    valid_keys.add('namespace')
    extra_keys = result_keys.difference(valid_keys)
    assert not extra_keys, \
        'Found extra invalid keys in the result. extra_keys=%s, result=%s, valid_keys=%s' % \
        (extra_keys, result, valid_keys)

    assert_keys(result, namespace='galaxy', name='some_name',
                version='1.2.4', scm=None, src='galaxy.role')


# comments in yaml_parse.py indicate src='galaxy.role,version,name' is supposed to work
def test_yaml_parse_a_dict_with_conflicts():
    spec = {'name': 'some_name1',
            'version': '1.2.3',
            'src': 'galaxy.role,1.0.0,some_name2'}
    result = parse_spec(spec)

    assert_keys(result, namespace='galaxy', name='some_name1',
                version='1.2.3', scm=None, src='galaxy.role,1.0.0,some_name2')


def test_yaml_parse_a_old_style_role_dict():
    spec = {'role': 'some_role',
            'version': '1.2.3',
            'src': 'galaxy.role'}
    result = parse_spec(spec)

    # FIXME: requiring a different set of asserts to test the results for the role
    #        case points to this method doing too many things, being passed too many different things,
    #        and returning too many different things
    name = 'some_role'
    src = 'galaxy.role'
    assert isinstance(result, dict)
    assert result['name'] == name, \
        'content_spec name=%s does not match expected name=%s' % (result['name'], name)
    assert result['version'] == '1.2.3'
    assert result['src'] == src, \
        'content_spec src=%s does not match expected src=%s' % (result['src'], src)


# FIXME: I'm not real sure what the result of this is supposed to be
def test_yaml_parse_a_comma_sep_style_role_dict_with_version():
    src = 'galaxy.role,1.2.3'
    spec = {'src': src}
    result = parse_spec(spec, resolver=galaxy_content_spec.resolve)

    # FIXME: wtf is 'src' expected to look like here?
    assert_keys(result, namespace='galaxy', name='role', version='1.2.3',
                scm=None, src='galaxy.role,1.2.3')


# FIXME: I'm not real sure what the result of this is supposed to be
def test_yaml_parse_a_comma_sep_style_role_dict_with_name_version():
    src = 'galaxy.role,1.2.3,some_role'
    spec = {'src': src}
    result = parse_spec(spec, resolver=galaxy_content_spec.resolve)

    # FIXME: wtf is 'src' expected to look like here?
    assert_keys(result, namespace='galaxy', name='some_role', version='1.2.3', scm=None, src=src)
