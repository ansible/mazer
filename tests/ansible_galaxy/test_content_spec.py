import logging
import os
import tempfile
import pytest

from ansible_galaxy import content_spec
from ansible_galaxy import exceptions
from ansible_galaxy.models.content_spec import ContentSpec

log = logging.getLogger(__name__)

content_spec_from_string_cases = \
    [
        {'spec': 'geerlingguy.apache',
         'expected': ContentSpec(name='apache', namespace='geerlingguy')},
        {'spec': 'geerlingguy.apache,2.1.1',
         'expected': ContentSpec(name='apache', namespace='geerlingguy', version='2.1.1')},
        {'spec': 'testing.ansible-testing-content',
         'expected': ContentSpec(name='ansible-testing-content', namespace='testing')},
        {'spec': 'testing.ansible-testing-content,name=testing-content',
         'expected': ContentSpec(name='testing-content', namespace='testing')},
        {'spec': 'alikins.awx',
         'expected': ContentSpec(name='awx', namespace='alikins')},
        {'spec': 'testing.ansible-testing-content,1.2.3,name=testing-content',
         'expected': ContentSpec(name='testing-content', namespace='testing', version='1.2.3')},
        {'spec': 'testing.ansible-testing-content,1.2.3,also-testing-content,stuff',
         'expected': ContentSpec(name='also-testing-content', namespace='testing', version='1.2.3')},
        # for git/tar/url, we dont try to guess the namespace, so the expected result is namespace=None
        # here. cli adds a namespace from --namespace here.
        {'spec': 'git+https://github.com/geerlingguy/ansible-role-apache.git,version=2.0.0',
         'expected': ContentSpec(name='ansible-role-apache', namespace=None, version='2.0.0',
                                 scm='git')},
        {'spec': 'git+https://mazertestuser@github.com/geerlingguy/ansible-role-apache.git,version=2.0.0',
         'expected': ContentSpec(name='ansible-role-apache', namespace=None, version='2.0.0',
                                 scm='git', fetch_method=content_spec.FetchMethods.SCM_URL)},
        # A path to a file without a dot in it's name. It's path will include where the tests are run from
        # so specify a ',name=' to provide a predictable name (otherwise it would be the full path)
        {'spec': '%s,name=the_license' % os.path.normpath(os.path.join(os.path.dirname(__file__), '../../LICENSE')),
         'expected': ContentSpec(name='the_license', namespace=None,
                                 fetch_method=content_spec.FetchMethods.LOCAL_FILE)},
        {'spec': 'https://docs.ansible.com,name=the_docs',
         'expected': ContentSpec(name='the_docs', namespace=None,
                                 scm=None, fetch_method=content_spec.FetchMethods.REMOTE_URL)},
        # 'foo',
        # 'foo,1.2.3',
        # 'foo,version=1.2.3',
        # 'foo,1.2.3,somename',
        # 'foo,1.2.3,name=somename',
        # 'foo,1.2.3,somename,somescm',
        # 'foo,1.2.3,somename,somescm,someextra'
    ]


@pytest.fixture(scope='module',
                params=content_spec_from_string_cases,
                ids=[x['spec'] for x in content_spec_from_string_cases])
def content_spec_case(request):
    yield request.param


def test_content_spec_from_string(content_spec_case):
    result = content_spec.content_spec_from_string(content_spec_case['spec'])
    log.debug('spec=%s result=%s exp=%s', content_spec_case['spec'], result, content_spec_case['expected'])

    # assert attr.asdict(result) == attr.asdict(content_spec_case['expected'])
    assert result == content_spec_case['expected']


def test_content_spec_editable():
    tmpdir = tempfile.mkdtemp()
    result = content_spec.content_spec_from_string(tmpdir, editable=True)
    os.rmdir(tmpdir)
    assert result.name == tmpdir
    assert result.fetch_method == 'EDITABLE'


@pytest.mark.xfail(raises=exceptions.GalaxyError)
def test_content_spec_fail():
    content_spec.content_spec_from_string('foo.')


@pytest.mark.xfail(raises=exceptions.GalaxyError)
def test_content_editable_fail():
    content_spec.content_spec_from_string('foo', editable=True)
