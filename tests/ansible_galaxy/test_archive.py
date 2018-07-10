
import logging
import mock
import os
import shutil
import tarfile
import tempfile
import pprint

from ansible_galaxy import archive
from ansible_galaxy import exceptions
from ansible_galaxy.models.content import GalaxyContentMeta


log = logging.getLogger(__name__)

TMP_PREFIX = 'tmp_mazer_test_archive_'


def test_extract_file_empty():
    tmp_tar = tempfile.TemporaryFile(prefix=TMP_PREFIX)
    # TODO: replace with tmpdir fixture
    tmp_dir = tempfile.mkdtemp(prefix=TMP_PREFIX)

    tar_file = tarfile.TarFile(
                               # name='some-top-level',
                               mode='w',
                               fileobj=tmp_tar)

    log.debug('tar_file.members: %s', tar_file.members)

    tar_file.close()

    # for pathname in tar_example1:
    pathname = 'this_should_not_be_in_empty_tar.yml'
    file_to_extract = {'archive_member': tarfile.TarInfo(name='foo'),
                       'dest_dir': tmp_dir,
                       'dest_filename': pathname,
                       'force_overwrite': True}

    log.debug('files_to_extract: %s', pprint.pformat(file_to_extract))

    read_tar_file = tarfile.TarFile.open(fileobj=tmp_tar, mode='r')

    try:
        res = archive.extract_file(read_tar_file, file_to_extract=file_to_extract)
        log.debug('res: %s', res)
        log.debug('listdir(%s): %s', tmp_dir, os.listdir(tmp_dir))
    except exceptions.GalaxyArchiveError as e:
        log.exception(e)
        return
    except tarfile.ReadError as e:
        log.exception(e)
        return
    finally:
        tmp_tar.close()
        read_tar_file.close()
        shutil.rmtree(tmp_dir)


def test_extract_file_foo():
    tmp_tar_fo = tempfile.NamedTemporaryFile(delete=False, prefix='dddddddddddddd')
    tmp_member_fo = tempfile.NamedTemporaryFile(delete=False, prefix='cccccccccc')
    # TODO: replace with tmpdir fixture
    tmp_dir = tempfile.mkdtemp(prefix='fffffcccc')

    tar_file = tarfile.TarFile.open(mode='w',
                                    fileobj=tmp_tar_fo)
    # fileobj=tmp_tar)

    files_to_extract = []

    # for pathname in tar_example1:
    pathname = 'foo_blip.yml'
    member = tarfile.TarInfo(pathname)
    tar_file.addfile(member, tmp_member_fo)

    log.debug('tar_file2 members: %s', tar_file.getmembers())
    tar_file.close()

    item = {'archive_member': member,
            'dest_dir': tmp_dir,
            'dest_filename': pathname,
            'force_overwrite': False}

    files_to_extract.append(item)
    log.debug('files_to_extract: %s', pprint.pformat(files_to_extract))

    read_tar_file = tarfile.TarFile.open(name=tmp_tar_fo.name, mode='r')
    res = archive.extract_file(read_tar_file, file_to_extract=item)
    log.debug('res: %s', res)

    log.debug('listdir: %s', os.listdir(tmp_dir))
    assert pathname in os.listdir(tmp_dir)

    os.unlink(tmp_tar_fo.name)
    read_tar_file.close()
    tmp_tar_fo.close()
    tmp_member_fo.close()
    os.unlink(tmp_member_fo.name)
    shutil.rmtree(tmp_dir)


def test_extract_files():
    tmp_tar_fo = tempfile.NamedTemporaryFile(delete=False, prefix='dddddddddddddd')
    tmp_member_fo = tempfile.NamedTemporaryFile(delete=False, prefix='cccccccccc')
    # TODO: replace with tmpdir fixture
    tmp_dir = tempfile.mkdtemp(prefix='fffffcccc')

    tar_file = tarfile.TarFile.open(mode='w',
                                    fileobj=tmp_tar_fo)
    # fileobj=tmp_tar)

    files_to_extract = []

    # for pathname in tar_example1:
    pathnames = ['foo_blip.yml',
                 'bar_foo.yml']

    for pathname in pathnames:
        member = tarfile.TarInfo(pathname)
        tar_file.addfile(member, tmp_member_fo)

        item = {'archive_member': member,
                'dest_dir': tmp_dir,
                'dest_filename': pathname,
                'force_overwrite': False}

        files_to_extract.append(item)

    log.debug('tar_file2 members: %s', tar_file.getmembers())
    tar_file.close()

    log.debug('files_to_extract: %s', pprint.pformat(files_to_extract))

    read_tar_file = tarfile.TarFile.open(name=tmp_tar_fo.name, mode='r')
    res_gen = archive.extract_files(read_tar_file, files_to_extract=files_to_extract)
    res = list(res_gen)
    log.debug('res: %s', res)

    log.debug('listdir: %s', os.listdir(tmp_dir))
    assert pathname in os.listdir(tmp_dir)

    os.unlink(tmp_tar_fo.name)
    read_tar_file.close()
    tmp_tar_fo.close()
    tmp_member_fo.close()
    os.unlink(tmp_member_fo.name)
    shutil.rmtree(tmp_dir)


def test_extract_file(mocker):
    # FIXME: rm out of tests tar file example
    # FIXME: generate a test tarfile
    tar_file_mock = mocker.MagicMock(spec_set=tarfile.TarFile)
    # TODO: replace with tmpdir fixture
    tmp_dir = tempfile.mkdtemp(prefix=TMP_PREFIX)

    files_to_extract = []
    # for pathname in tar_example1:
    pathname = 'roles/test-role-d/handlers/main.yml'
    top_dir = 'ansible-content-archive'

    dest_dir = os.path.join(tmp_dir, 'extracted_stuff')

    member = tarfile.TarInfo(os.path.join(top_dir, pathname))

    item = {'archive_member': member,
            'dest_dir': dest_dir,
            'dest_filename': pathname,
            'force_overwrite': True}

    log.debug('files_to_extract: %s', pprint.pformat(files_to_extract))

    res = archive.extract_file(tar_file_mock, file_to_extract=item)

    log.debug('tar_file_mock: %s', tar_file_mock)
    log.debug('tar_file_mock.call_args_list: %s', tar_file_mock.call_args_list)
    log.debug('tar_file_mock.method_calls: %s', tar_file_mock.method_calls)
    log.debug('res: %s', res)

    assert pathname in res
    # log.debug('%s contents: %s', tmp_dir, glob.glob(dest_dir, '**', recursive=True))
    shutil.rmtree(tmp_dir)


def test_extract_file_exists(mocker):
    tar_file_mock = mocker.MagicMock(spec_set=tarfile.TarFile)
    # TODO: replace with tmpdir fixture
    tmp_dir = tempfile.mkdtemp(prefix=TMP_PREFIX)

    files_to_extract = []
    # for pathname in tar_example1:
    pathname = 'roles/test-role-d/handlers/main.yml'
    top_dir = 'ansible-content-archive'

    dest_dir = os.path.join(tmp_dir, 'extracted_stuff')

    def faux_exists(path):
        if path.startswith(dest_dir):
            return True
        return False

    mocker.patch('ansible_galaxy.archive.os.path.exists',
                 side_effect=faux_exists)

    member = tarfile.TarInfo(os.path.join(top_dir, pathname))

    item = {'archive_member': member,
            'dest_dir': dest_dir,
            'dest_filename': pathname,
            'force_overwrite': False}

    log.debug('files_to_extract: %s', pprint.pformat(files_to_extract))

    try:
        archive.extract_file(tar_file_mock, file_to_extract=item)
    except exceptions.GalaxyClientError as e:
        log.exception(e)
        return
    finally:
        shutil.rmtree(tmp_dir)

    assert False, 'Expected a GalaxyClientError because the file to extract already exists, but that did not happen'


def test_extract_files_tmp(mocker):
    # FIXME: rm out of tests tar file example
    # FIXME: generate a test tarfile
    # tar_file = tarfile.TarFile.open(name='/tmp/alikins.testing-content.tar.gz',
    #                                mode='r')

    tar_file_mock = mocker.MagicMock(spec_set=tarfile.TarFile)

    # TODO: replace with tmpdir fixture
    tmp_dir = tempfile.mkdtemp(prefix=TMP_PREFIX)

    files_to_extract = []
    # for pathname in tar_example1:
    top_dir = 'ansible-content-archive'

    dest_dir = os.path.join(tmp_dir, 'extracted_stuff')

    path_list = ['roles/test-role-d/handlers/main.yml',
                 'roles/test-role-a/handlers/main.yml']

    for pathname in path_list:
        member_path = os.path.join(top_dir, pathname)
        member = tarfile.TarInfo(member_path)

        item = {'archive_member': member,
                'dest_dir': dest_dir,
                'dest_filename': pathname,
                'force_overwrite': True}

        files_to_extract.append(item)

    log.debug('files_to_extract: %s', pprint.pformat(files_to_extract))

    res = archive.extract_files(tar_file_mock, files_to_extract=files_to_extract)

    log.debug('tar_file_mock: %s', tar_file_mock)
    log.debug('tar_file_mock.call_args_list: %s', tar_file_mock.call_args_list)
    log.debug('tar_file_mock.method_calls: %s', tar_file_mock.method_calls)
    log.debug('res: %s', list(res))
    # log.debug('%s contents: %s', tmp_dir, glob.glob(dest_dir, '**', recursive=True))
    log.debug('%s contents: %s', tmp_dir, list(os.walk(dest_dir)))
    shutil.rmtree(tmp_dir)


foo = {'content_archive_type': 'multi-content',
       #       'content_meta': GalaxyContentMeta(name=alikins.ansible-testing-content, version=3.1.0, src=alikins.ansible-testing-content,
       #                       scm=None, content_type=all, content_dir=None, content_sub_dir=None, path=/home/adrian/.ansible/content, requires_meta_main=None),
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
                                          content_meta=GalaxyContentMeta(namespace='alikins',
                                                                         name="ansible-testing-content",
                                                                         version="3.1.0",
                                                                         src="alikins.ansible-testing-content",
                                                                         scm=None,
                                                                         content_type="all",
                                                                         content_dir=None,
                                                                         content_sub_dir=None,
                                                                         path="/home/adrian/.ansible/content",
                                                                         requires_meta_main=None),
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


def _tar_members(file_list):
    members = []
    for file_name in file_list:
        members.append(tarfile.TarInfo(name=file_name))

    return members


def test_find_members_by_fnmatch():
    members = _tar_members(tar_example1)

    len_members = len(members)
    match_pattern = '*'
    res = archive.filter_members_by_fnmatch(members, match_pattern)

    assert len(res) == len_members, 'filtering on "*" missed some archive members'
    assert isinstance(res, list)

    action_match_pattern = '*/action_plugins/*'
    res = archive.filter_members_by_fnmatch(members, action_match_pattern)

    assert len(res) == 1, 'filtering on "%s" should find one action plugin' % action_match_pattern


def test_find_members_by_content_type():
    members = _tar_members(tar_example1)

    res = archive.filter_members_by_content_type(members, 'multi-content', 'role')

    log.debug('res: %s', pprint.pformat(res))

    filenames = [x.name for x in res]
    assert 'ansible-testing-content-master/roles/test-role-d/vars/main.yml' in filenames
    assert 'ansible-testing-content-master/strategy_plugins/free.py' not in filenames


def test_find_members_by_content_type_role_archive():
    members = _tar_members(tar_example1)
    len_members = len(members)

    res = archive.filter_members_by_content_type(members, 'role', 'role')

    log.debug('res: %s', pprint.pformat(res))

    filenames = [x.name for x in res]
    assert 'ansible-testing-content-master/roles/test-role-d/vars/main.yml' in filenames
    # a role archive should not having anything filtered out
    assert len_members == len(res)
