import logging
import os

from ansible_galaxy import exceptions
from ansible_galaxy.actions import list as list_action

log = logging.getLogger(__name__)


def display_callback(msg, **kwargs):
    log.debug(msg)


# TODO: make a fixture that sets up a faux installed_*_db

def test__list(galaxy_context, mocker):
    mocker.patch('ansible_galaxy.installed_namespaces_db.get_namespace_paths',
                 return_value=iter(['ns_blip', 'ns_foo']))
    mocker.patch('ansible_galaxy.installed_repository_db.get_repository_paths',
                 return_value=iter(['n_bar', 'n_baz']))

    mocker.patch('ansible_galaxy.repository.os.path.isdir',
                 return_value=True)

    mocker.patch('ansible_galaxy.installed_content_item_db.python_content_path_iterator',
                 return_value=iter(['/dev/null/content/ns_foo/n_bar/roles/role-1',
                                    '/dev/null/content/ns_blip/n_bar/roles/role-3',
                                    '/dev/null/content/ns_blip/n_baz/roles/role-2']))

    res = list_action._list(galaxy_context,
                            display_callback=display_callback)

    # log.debug('res: %s', pprint.pformat(res))

    assert isinstance(res, list)
    assert 'ns_blip.n_bar' in [x['installed_repository'].repository_spec.label for x in res]


def test_list_empty_roles_paths(galaxy_context):

    try:
        list_action.list_action(galaxy_context,
                                display_callback=display_callback)
    except exceptions.GalaxyError as e:
        log.debug(e, exc_info=True)
        raise


def test_list_no_content_dir(galaxy_context):
    galaxy_context.collections_path = os.path.join(galaxy_context.collections_path, 'doesntexist')
    res = list_action.list_action(galaxy_context,
                                  display_callback=display_callback)

    # TODO: list should probably return non-zero if galaxy_context.collections_path doesnt exist,
    #       but should probaly initially check that when creating galaxy_context
    assert res == 0


def test_format_as_lockfile_empty():
    repo_list = []
    res = list_action.format_as_lockfile(repo_list)
    log.debug('res: |%s|', res)
    assert res == ''


def test_format_as_lockfile(mocker):
    repo_list = []
    mock_installed = mocker.MagicMock()
    mock_installed.repository_spec.version = '1.2.3'
    mock_installed.repository_spec.label = 'testns.testcollection'
    mock_installed2 = mocker.MagicMock()
    mock_installed2.repository_spec.version = '0.0.1'
    mock_installed2.repository_spec.label = 'example.randomjunk'

    repo_dict = {'content_items': {},
                 'installed_repository': mock_installed
                 }
    repo_list.append(repo_dict)
    repo_list.append({'content_items': {},
                      'installed_repository': mock_installed2})
    res = list_action.format_as_lockfile(repo_list)
    log.debug('res: |%s|', res)

    assert 'testns.testcollection' in res
