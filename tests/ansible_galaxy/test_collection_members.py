import collections
import logging
import os

import pprint

from ansible_galaxy import collection_members

log = logging.getLogger(__name__)
pf = pprint.pformat

hello_path = os.path.join(os.path.dirname(__file__), 'collection_examples', 'hello')


def test_file_walker_cwd():
    cwd = os.getcwd()
    git_dir = os.path.join(cwd, '.git/')

    file_walker = collection_members.FileWalker(cwd, exclude_patterns=collection_members.DEFAULT_IGNORE_PATTERNS+['*.json'])
    file_names = file_walker.walk()
    for file_name in file_names:
        assert not file_name.startswith(git_dir), '%s found in %s but should be excluded by default' % (git_dir, file_name)
        assert '__pycache__' not in file_name, '__pycache__ found in path %s, but __pycache__ dirs should be ignored by default' % (file_name)


def test_collection_members_init():
    # gather files from mazer src dir, not really a role
    collection_path = os.path.join(os.getcwd())
    file_walker = collection_members.FileWalker(collection_path)
    coll_members = collection_members.CollectionMembers(walker=file_walker)
    log.debug('coll_members: %s', coll_members)

    members = coll_members.run()

    # NOTE: no reason .run() couldn't return a iterable/generator this is not
    #       actually an (sub)instance of collections.Iterable, but it is to catch
    #       when I forget to yield
    assert isinstance(members, collections.Iterable)

    members_list = list(members)
    assert isinstance(members_list, list)


def test_collection_members_post_filter():

    file_walker = collection_members.FileWalker(hello_path, exclude_patterns=['*.json'])
    coll_members = collection_members.CollectionMembers(walker=file_walker)

    members = coll_members.run()

    # just to trigger the iteration
    members_list = list(members)
    assert isinstance(members_list, list)

    log.debug('members_list: %s', pf(members_list))

    some_json_path = os.path.join(hello_path, 'some_json_file.json')
    assert some_json_path not in members_list
