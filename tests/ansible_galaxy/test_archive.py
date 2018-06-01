
import logging
import tarfile
import tempfile
import mock

from ansible_galaxy import archive
from ansible_galaxy.models.content import GalaxyContentMeta

log = logging.getLogger(__name__)


def test_find_content_type_subdirs_empty():
    tmp_tar = tempfile.TemporaryFile()

    tar_file = tarfile.TarFile(name='some-top-level',
                               mode='w',
                               fileobj=tmp_tar)

    tar_file_members = tar_file.getmembers()

    res = archive.find_content_type_subdirs(tar_file_members)
    log.debug('res: %s', res)

    assert isinstance(res, list)
    assert res == []
    assert not res


foo = {'content_archive_type': 'multi-content',
#       'content_meta': GalaxyContentMeta(name=alikins.ansible-testing-content, version=3.1.0, src=alikins.ansible-testing-content, scm=None, content_type=all, content_dir=None, content_sub_dir=None, path=/home/adrian/.ansible/content, requires_meta_main=None),
       'content_type': None,
       'content_type_requires_meta': True,
       'display_callback': None,
       'extract_to_path': '/home/adrian/.ansible/content',
       'file_name': None,
 #      'files_to_extract': [<TarInfo 'ansible-testing-content-3.1.0/library/elasticsearch_plugin.py' at 0x7f5b549c9c90>,
 #                           <TarInfo 'ansible-testing-content-3.1.0/library/riak.py' at 0x7f5b549c9e50>],
       'force_overwrite': True,
       'install_all_content': False,
       'install_content_type': 'module',
       'parent_dir': None,
 #      'tar_file_obj': <tarfile.TarFile object at 0x7f5b549c9950>
       }


def test_extract_by_content_type():
    # tar_file_obj = tarfile.TarFile()
    members = [tarfile.TarInfo(name='foo')]
    mock_tar_file_obj = mock.Mock(members=members)
    res = archive.extract_by_content_type(tar_file_obj=mock_tar_file_obj,
                                          parent_dir=None,
                                          content_meta=GalaxyContentMeta(name="alikins.ansible-testing-content",
                                                                         version="3.1.0",
                                                                         src="alikins.ansible-testing-content",
                                                                         scm=None,
                                                                         content_type="all",
                                                                         content_dir=None,
                                                                         content_sub_dir=None,
                                                                         path="/home/adrian/.ansible/content",
                                                                         requires_meta_main=None),
                                          install_content_type="module",
                                          install_all_content=False,
                                          files_to_extract=members,
                                          extract_to_path='/home/adrian/.ansible/content')

    log.debug('res: %s', res)


tar_example1 = [
    'ansible-testing-content-master/.gitignore',
    'ansible-testing-content-master/LICENSE',
    'ansible-testing-content-master/README.md',
    'ansible-testing-content-master/action_plugins',
    'ansible-testing-content-master/action_plugins/add_host.py',
    'ansible-testing-content-master/filter_plugins',
    'ansible-testing-content-master/filter_plugins/json_query.py',
    'ansible-testing-content-master/filter_plugins/mathstuff.py',
    'ansible-testing-content-master/library',
    'ansible-testing-content-master/library/elasticsearch_plugin.py',
    'ansible-testing-content-master/library/kibana_plugin.py',
    'ansible-testing-content-master/library/mysql_db.py',
    'ansible-testing-content-master/library/mysql_replication.py',
    'ansible-testing-content-master/library/mysql_user.py',
    'ansible-testing-content-master/library/mysql_variables.py',
    'ansible-testing-content-master/library/redis.py',
    'ansible-testing-content-master/library/riak.py',
    'ansible-testing-content-master/module_utils',
    'ansible-testing-content-master/module_utils/common.py',
    'ansible-testing-content-master/module_utils/helper.py',
    'ansible-testing-content-master/module_utils/inventory.py',
    'ansible-testing-content-master/module_utils/lookup.py',
    'ansible-testing-content-master/module_utils/raw.py',
    'ansible-testing-content-master/module_utils/scale.py',
    'ansible-testing-content-master/roles',
    'ansible-testing-content-master/roles/ansible-role-foobar',
    'ansible-testing-content-master/roles/ansible-role-foobar/.travis.yml',
    'ansible-testing-content-master/roles/ansible-role-foobar/README.md',
    'ansible-testing-content-master/roles/ansible-role-foobar/defaults',
    'ansible-testing-content-master/roles/ansible-role-foobar/defaults/main.yml',
    'ansible-testing-content-master/roles/ansible-role-foobar/handlers',
    'ansible-testing-content-master/roles/ansible-role-foobar/handlers/main.yml',
    'ansible-testing-content-master/roles/ansible-role-foobar/meta',
    'ansible-testing-content-master/roles/ansible-role-foobar/meta/main.yml',
    'ansible-testing-content-master/roles/ansible-role-foobar/tasks',
    'ansible-testing-content-master/roles/ansible-role-foobar/tasks/main.yml',
    'ansible-testing-content-master/roles/ansible-role-foobar/tests',
    'ansible-testing-content-master/roles/ansible-role-foobar/tests/inventory',
    'ansible-testing-content-master/roles/ansible-role-foobar/tests/test.yml',
    'ansible-testing-content-master/roles/ansible-role-foobar/vars',
    'ansible-testing-content-master/roles/ansible-role-foobar/vars/main.yml',
    'ansible-testing-content-master/roles/ansible-test-role-1',
    'ansible-testing-content-master/roles/ansible-test-role-1/.travis.yml',
    'ansible-testing-content-master/roles/ansible-test-role-1/README.md',
    'ansible-testing-content-master/roles/ansible-test-role-1/defaults',
    'ansible-testing-content-master/roles/ansible-test-role-1/defaults/main.yml',
    'ansible-testing-content-master/roles/ansible-test-role-1/handlers',
    'ansible-testing-content-master/roles/ansible-test-role-1/handlers/main.yml',
    'ansible-testing-content-master/roles/ansible-test-role-1/meta',
    'ansible-testing-content-master/roles/ansible-test-role-1/meta/main.yml',
    'ansible-testing-content-master/roles/ansible-test-role-1/tasks',
    'ansible-testing-content-master/roles/ansible-test-role-1/tasks/main.yml',
    'ansible-testing-content-master/roles/ansible-test-role-1/tests',
    'ansible-testing-content-master/roles/ansible-test-role-1/tests/inventory',
    'ansible-testing-content-master/roles/ansible-test-role-1/tests/test.yml',
    'ansible-testing-content-master/roles/ansible-test-role-1/vars',
    'ansible-testing-content-master/roles/ansible-test-role-1/vars/main.yml',
    'ansible-testing-content-master/roles/test-role-a',
    'ansible-testing-content-master/roles/test-role-a/defaults',
    'ansible-testing-content-master/roles/test-role-a/defaults/main.yml',
    'ansible-testing-content-master/roles/test-role-a/handlers',
    'ansible-testing-content-master/roles/test-role-a/handlers/main.yml',
    'ansible-testing-content-master/roles/test-role-a/meta',
    'ansible-testing-content-master/roles/test-role-a/meta/main.yml',
    'ansible-testing-content-master/roles/test-role-a/tasks',
    'ansible-testing-content-master/roles/test-role-a/tasks/main.yml',
    'ansible-testing-content-master/roles/test-role-a/tests',
    'ansible-testing-content-master/roles/test-role-a/tests/inventory',
    'ansible-testing-content-master/roles/test-role-a/tests/test.yml',
    'ansible-testing-content-master/roles/test-role-a/vars',
    'ansible-testing-content-master/roles/test-role-a/vars/main.yml',
    'ansible-testing-content-master/roles/test-role-b',
    'ansible-testing-content-master/roles/test-role-b/.travis.yml',
    'ansible-testing-content-master/roles/test-role-b/README.md',
    'ansible-testing-content-master/roles/test-role-b/defaults',
    'ansible-testing-content-master/roles/test-role-b/defaults/main.yml',
    'ansible-testing-content-master/roles/test-role-b/handlers',
    'ansible-testing-content-master/roles/test-role-b/handlers/main.yml',
    'ansible-testing-content-master/roles/test-role-b/meta',
    'ansible-testing-content-master/roles/test-role-b/meta/main.yml',
    'ansible-testing-content-master/roles/test-role-b/tasks',
    'ansible-testing-content-master/roles/test-role-b/tasks/main.yml',
    'ansible-testing-content-master/roles/test-role-b/tests',
    'ansible-testing-content-master/roles/test-role-b/tests/inventory',
    'ansible-testing-content-master/roles/test-role-b/tests/test.yml',
    'ansible-testing-content-master/roles/test-role-b/vars',
    'ansible-testing-content-master/roles/test-role-b/vars/main.yml',
    'ansible-testing-content-master/roles/test-role-c',
    'ansible-testing-content-master/roles/test-role-c/.travis.yml',
    'ansible-testing-content-master/roles/test-role-c/README.md',
    'ansible-testing-content-master/roles/test-role-c/defaults',
    'ansible-testing-content-master/roles/test-role-c/defaults/main.yml',
    'ansible-testing-content-master/roles/test-role-c/handlers',
    'ansible-testing-content-master/roles/test-role-c/handlers/main.yml',
    'ansible-testing-content-master/roles/test-role-c/meta',
    'ansible-testing-content-master/roles/test-role-c/meta/main.yml',
    'ansible-testing-content-master/roles/test-role-c/tasks',
    'ansible-testing-content-master/roles/test-role-c/tasks/main.yml',
    'ansible-testing-content-master/roles/test-role-c/tests',
    'ansible-testing-content-master/roles/test-role-c/tests/inventory',
    'ansible-testing-content-master/roles/test-role-c/tests/test.yml',
    'ansible-testing-content-master/roles/test-role-c/vars',
    'ansible-testing-content-master/roles/test-role-c/vars/main.yml',
    'ansible-testing-content-master/roles/test-role-d',
    'ansible-testing-content-master/roles/test-role-d/.travis.yml',
    'ansible-testing-content-master/roles/test-role-d/README.md',
    'ansible-testing-content-master/roles/test-role-d/defaults',
    'ansible-testing-content-master/roles/test-role-d/defaults/main.yml',
    'ansible-testing-content-master/roles/test-role-d/handlers',
    'ansible-testing-content-master/roles/test-role-d/handlers/main.yml',
    'ansible-testing-content-master/roles/test-role-d/meta',
    'ansible-testing-content-master/roles/test-role-d/meta/main.yml',
    'ansible-testing-content-master/roles/test-role-d/tasks',
    'ansible-testing-content-master/roles/test-role-d/tasks/main.yml',
    'ansible-testing-content-master/roles/test-role-d/tests',
    'ansible-testing-content-master/roles/test-role-d/tests/inventory',
    'ansible-testing-content-master/roles/test-role-d/tests/test.yml',
    'ansible-testing-content-master/roles/test-role-d/vars',
    'ansible-testing-content-master/roles/test-role-d/vars/main.yml',
    'ansible-testing-content-master/strategy_plugins',
    'ansible-testing-content-master/strategy_plugins/debug.py',
    'ansible-testing-content-master/strategy_plugins/free.py',
    'ansible-testing-content-master/strategy_plugins/linear.py']


# def test_foo():
#
#    members = []
#    for file_name in tar_example1:
#        members.append(tarfile.TarInfo(name=file_name))
#
#    res = archive.find_content_type_subdirs(members)
#    import pprint
#    log.debug('res: %s', pprint.pformat(res))

#    assert isinstance(res, list)
#    assert 'roles' in res
#    assert 'action_plugins' in res
#    assert 'library' in res
#    assert 'modules' not in res
