import logging
import os

from ansible_galaxy.actions import migrate_role
from ansible_galaxy import collection_info
from ansible_galaxy.models.collection_info import CollectionInfo
from ansible_galaxy.models.migrate_role_context import MigrateRoleContext

log = logging.getLogger(__name__)


OLD_SCHOOL_ROLE_PATH = os.path.join(os.path.dirname(__file__), '../', '../', 'data', 'roles', 'old_school_role')
COL_NAMESPACE = 'some_namespace'
COL_NAME = 'some_name'
COL_VERSION = '9.1.9'


def display_callback(msg, **kwargs):
    log.debug(msg)


def _migrate_role(output_path,
                  display_callback=display_callback,
                  role_path=OLD_SCHOOL_ROLE_PATH,
                  collection_namespace=COL_NAMESPACE,
                  collection_name=COL_NAME,
                  collection_version=COL_VERSION):

    migrate_role_context = MigrateRoleContext(role_path=role_path,
                                              output_path=output_path,
                                              collection_namespace=collection_namespace,
                                              collection_name=collection_name,
                                              collection_version=collection_version)
    res = migrate_role.migrate(migrate_role_context=migrate_role_context,
                               display_callback=display_callback)

    return res, migrate_role_context


def test_migrate_role_galaxy_yml(tmpdir):
    output_path = tmpdir.mkdir('mazer_test_migrate_role_action_test_migrate_role')

    res, migrate_role_context = _migrate_role(output_path=output_path.strpath)

    assert res == 0
    assert os.path.isdir(output_path.strpath)

    galaxy_yml_path = os.path.join(output_path.strpath, 'galaxy.yml')

    assert os.path.isfile(galaxy_yml_path)

    with open(galaxy_yml_path, 'r') as cfd:
        col_info = collection_info.load(cfd)

    log.debug('col_info: %s', col_info)

    assert isinstance(col_info, CollectionInfo)
    assert col_info.namespace == COL_NAMESPACE
    assert col_info.name == COL_NAME
    assert col_info.version == COL_VERSION
    assert isinstance(col_info.authors, list)
    assert isinstance(col_info.dependencies, dict)

# TODO: test missing role_path, output_path doesnt exist,
#       role loading errors, collection_info validation errors
