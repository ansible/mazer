import logging
import os
import tempfile
import pytest

from ansible_galaxy import repository_spec
from ansible_galaxy import exceptions
from ansible_galaxy.models.repository_spec import RepositorySpec, FetchMethods

log = logging.getLogger(__name__)

repo_spec_from_string_cases = \
    [
        {'spec': 'geerlingguy.apache',
         'expected': RepositorySpec(name='apache', namespace='geerlingguy',
                                    version=None, fetch_method=FetchMethods.GALAXY_URL)},
        {'spec': 'geerlingguy.apache,2.1.1',
         'expected': RepositorySpec(name='apache', namespace='geerlingguy',
                                    version='2.1.1', fetch_method=FetchMethods.GALAXY_URL)},
        {'spec': 'testing.ansible-testing-content',
         'expected': RepositorySpec(name='ansible-testing-content', namespace='testing',
                                    version=None, fetch_method=FetchMethods.GALAXY_URL)},
        # {'spec': 'testing.ansible-testing-content,name=testing-content',
        # 'expected': RepositorySpec(name='testing-content', namespace='testing')},
        # {'spec': 'alikins.awx',
        # 'expected': RepositorySpec(name='awx', namespace='alikins')},
        {'spec': 'testing.ansible-testing-content,1.2.3,name=testing-content',
         'expected': RepositorySpec(name='testing-content', namespace='testing',
                                    version='1.2.3', fetch_method=FetchMethods.GALAXY_URL)},
        {'spec': 'testing.ansible-testing-content,1.2.3,also-testing-content,stuff',
         'expected': RepositorySpec(name='also-testing-content', namespace='testing',
                                    version='1.2.3', fetch_method=FetchMethods.GALAXY_URL)},
        # for git/tar/url, we dont try to guess the namespace, so the expected result is namespace=None
        # here. cli adds a namespace from --namespace here.
        {'spec': 'git+https://github.com/geerlingguy/ansible-role-apache.git,version=2.0.0',
         'expected': RepositorySpec(name='ansible-role-apache', namespace=None, version='2.0.0',
                                    scm='git', fetch_method=FetchMethods.SCM_URL)},
        {'spec': 'git+https://mazertestuser@github.com/geerlingguy/ansible-role-apache.git,version=2.0.0',
         'expected': RepositorySpec(name='ansible-role-apache', namespace=None, version='2.0.0',
                                    scm='git', fetch_method=FetchMethods.SCM_URL)},
        # A path to a file without a dot in it's name. It's path will include where the tests are run from
        # so specify a ',name=' to provide a predictable name (otherwise it would be the full path)
        # TODO: local file will attempt to load the contents now, so this test case doesn't make sense without mocking
        #       out something to exist at the path
        # {'spec': '%s,name=the_license' % os.path.normpath(os.path.join(os.path.dirname(__file__), '../../NOTLICENSE')),
        #  'expected': RepositorySpec(name='the_license', namespace=None,
        #                             version=None, fetch_method=FetchMethods.LOCAL_FILE)},
    ]


@pytest.fixture(scope='module',
                params=repo_spec_from_string_cases,
                ids=[x['spec'] for x in repo_spec_from_string_cases])
def repository_spec_case(request):
    yield request.param


def test_repository_spec_from_string(repository_spec_case):
    result = repository_spec.repository_spec_from_string(repository_spec_case['spec'])
    log.debug('spec=%s result=%s exp=%s', repository_spec_case['spec'], result, repository_spec_case['expected'])

    assert result == repository_spec_case['expected']


def test_repository_spec_editable():
    tmpdir = tempfile.mkdtemp()
    expected = os.path.basename(tmpdir)
    log.debug('expected: %s', expected)

    result = repository_spec.repository_spec_from_string(tmpdir, namespace_override='my_namespace', editable=True)
    os.rmdir(tmpdir)

    log.debug('result: %r', result)

    assert result.name == expected
    assert result.namespace == 'my_namespace'
    assert result.version is None
    assert result.src == tmpdir
    assert result.fetch_method == 'EDITABLE'


@pytest.mark.xfail(raises=exceptions.GalaxyError)
def test_repository_spec_fail():
    repository_spec.repository_spec_from_string('foo.')


@pytest.mark.xfail(raises=exceptions.GalaxyError)
def test_repository_editable_fail():
    repository_spec.repository_spec_from_string('foo', editable=True)
