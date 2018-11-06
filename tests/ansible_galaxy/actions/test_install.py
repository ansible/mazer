import logging
import mock

from ansible_galaxy.actions import install
from ansible_galaxy import exceptions
from ansible_galaxy import repository_spec
from ansible_galaxy import requirements
from ansible_galaxy.models.repository import Repository
from ansible_galaxy.models.repository_spec import RepositorySpec

log = logging.getLogger(__name__)


def display_callback(msg, **kwargs):
    log.debug(msg)


def test_install_repos_empty_requirements(galaxy_context):
    requirements_to_install = []

    ret = install.install_repositories(galaxy_context,
                                       requirements_to_install=requirements_to_install,
                                       display_callback=display_callback)

    log.debug('ret: %s', ret)
    assert isinstance(ret, list)
    assert ret == []


def test_install_repositories(galaxy_context, mocker):
    repo_spec = RepositorySpec(namespace='some_namespace', name='some_name')
    expected_repos = [Repository(repository_spec=repo_spec)]

    requirements_to_install = \
        requirements.from_requirement_spec_strings(['some_namespace.this_requires_some_name'])

    mocker.patch('ansible_galaxy.actions.install.install_repository',
                 return_value=expected_repos)

    ret = install.install_repositories(galaxy_context,
                                       requirements_to_install=requirements_to_install,
                                       display_callback=display_callback)

    log.debug('ret: %s', ret)
    assert isinstance(ret, list)
    assert ret == expected_repos


def test_install_repositories_no_deps_required(galaxy_context, mocker):
    needed_deps = []

    repository_specs_to_install = \
        [repository_spec.repository_spec_from_string('some_namespace.this_requires_nothing')]

    # mock out install_repository
    mocker.patch('ansible_galaxy.actions.install.install_repository',
                 return_value=[])

    ret = install.install_repositories(galaxy_context,
                                       requirements_to_install=repository_specs_to_install,
                                       display_callback=display_callback)

    log.debug('ret: %s', ret)
    assert isinstance(ret, list)
    assert ret == needed_deps


def test_verify_repository_specs_have_namespace_empty(galaxy_context):
    # will throw an exception if busted
    install._verify_requirements_repository_spec_have_namespaces([])


# even though 'blrp' isnt a valid spec, _build_content_set return something for now
def test_verify_repository_specs_have_namespace(galaxy_context):
    repository_spec = mock.Mock(requirement_spec=mock.Mock(namespace=None))
    try:
        install._verify_requirements_repository_spec_have_namespaces([repository_spec])
    except exceptions.GalaxyError as e:
        log.exception(e)
        return

    assert False, 'Expected a GalaxyError to be raised here since the repository_spec %s has no namespace or dots' % repository_spec
