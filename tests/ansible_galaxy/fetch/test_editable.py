
import logging
import os

from ansible_galaxy.config.defaults import COLLECTIONS_PYTHON_NAMESPACE
from ansible_galaxy.fetch import editable
from ansible_galaxy import requirements
from ansible_galaxy.models.requirement_spec import RequirementSpec

log = logging.getLogger(__name__)


def test_editable_fetch_find(galaxy_context, mocker, tmpdir):
    name = 'mazer_fetch_test_editable'
    namespace_override = 'some_editable_namespace'

    tmp_path = tmpdir.mkdir(name)

    more_reqs = requirements.from_dependencies_dict({tmp_path.strpath: '*'},
                                                    namespace_override=namespace_override,
                                                    editable=True)
    import pprint
    log.debug('more_reqs: %s', pprint.pformat(more_reqs))

    req_spec = more_reqs[0].requirement_spec

    fetcher = editable.EditableFetch(galaxy_context, req_spec)

    log.debug(fetcher)

    res = fetcher.find()
    log.debug('res: %s', res)

    assert isinstance(res, dict)
    assert res['content']['galaxy_namespace'] == namespace_override
    assert res['content']['repo_name'] == name
    assert res['custom']['real_path'] == tmp_path.strpath


def test_editable_fetch_fetch(galaxy_context, mocker, tmpdir):
    name = 'mazer_fetch_test_editable'
    namespace_override = 'some_editable_namespace'

    tmp_working_path = tmpdir.mkdir('some_working_tree')
    dest_tmp_path = tmp_working_path.mkdir('some_checkout')

    req_spec = RequirementSpec(namespace=namespace_override,
                               name=name,
                               fetch_method='EDITABLE',
                               src=dest_tmp_path,
                               version_spec='*')
    # RepositorySpec(namespace='some_editable_namespace', name='some_checkout',
    #                version=None, fetch_method='EDITABLE', scm=None,
    #                spec_string='/tmp/pytest-of-adrian/pytest-79/test_editable_fetch_fetch0/some_checkout',
    #                src='/tmp/pytest-of-adrian/pytest-79/test_editable_fetch_fetch0/some_checkout')
    log.debug('req_spec: %r', req_spec)

    fetcher = editable.EditableFetch(galaxy_context, req_spec)

    find_results = {'custom': {'real_path': dest_tmp_path.strpath},
                    'content': []}

    res = fetcher.fetch(find_results=find_results)
    log.debug('res: %s', res)

    expected_link_name = os.path.join(galaxy_context.collections_path,
                                      COLLECTIONS_PYTHON_NAMESPACE,
                                      namespace_override,
                                      name)
    log.debug('expected_link_name: %s', expected_link_name)

    assert isinstance(res, dict)
    assert res['archive_path'] == dest_tmp_path.strpath
    assert res['custom']['symlinked_repo_root'] == expected_link_name
