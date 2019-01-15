import logging
import pytest

from ansible_galaxy.models.collection_info import CollectionInfo

log = logging.getLogger(__name__)


def test_license_error():
    test_data = {
        'namespace': 'foo',
        'name': 'foo',
        'authors': ['chouseknecht'],
        'license': 'GPLv2',
        'version': '0.0.1',
        'description': 'unit testing thing',
    }
    with pytest.raises(ValueError) as exc:
        CollectionInfo(**test_data)
    assert 'license' in str(exc)


def test_required_error():
    test_data = {
        'namespace': 'foo',
        'authors': ['chouseknecht'],
        'license': 'GPL-3.0-or-later',
        'version': '0.0.1',
        'description': 'unit testing thing'
    }
    with pytest.raises(ValueError) as exc:
        CollectionInfo(**test_data)
    assert 'name' in str(exc) in str(exc)


def test_name_parse_error_dots_in_name():
    test_data = {'namespace': 'foo',
                 'name': 'foo.bar',
                 'authors': ['chouseknecht'],
                 'license': 'GPL-3.0-or-later',
                 'version': '0.0.1',
                 'description': 'unit testing thing'}

    # CollectionInfo(**test_data)
    # ValueError: Invalid collection metadata. Expecting 'name' and 'namespace' to not include any '.' but 'foo.bar' has a '.'
    error_re = r"Invalid collection metadata. Expecting 'name' and 'namespace' to not include any '\.' but 'foo\.bar' has a '\.'"
    with pytest.raises(ValueError,
                       match=error_re) as exc:
        CollectionInfo(**test_data)
    assert 'name' in str(exc)


def test_name_parse_error_other_chars_namespace():
    test_data = {'namespace': 'foo@blip',
                 'name': 'foo',
                 'authors': ['chouseknecht'],
                 'license': 'GPL-3.0-or-later',
                 'version': '0.0.1',
                 'description': 'unit testing thing'}

    # ValueError: Invalid collection metadata. Expecting 'name' and 'namespace' to contain alphanumeric characters,
    # '-', or '_' only but 'foo@blip' contains others"
    error_re = r"Invalid collection metadata. Expecting 'name' and 'namespace' to contain alphanumeric characters, "
    "'-', or '_' only but 'foo@blip' contains others"
    with pytest.raises(ValueError,
                       match=error_re) as exc:
        CollectionInfo(**test_data)
    assert 'foo@blip' in str(exc)


def test_name_parse_error_name_leading_underscore():
    test_data = {'namespace': 'foo',
                 'name': '_foo',
                 'authors': ['chouseknecht'],
                 'license': 'GPL-3.0-or-later',
                 'version': '0.0.1',
                 'description': 'unit testing thing'}

    # ValueError: Invalid collection metadata. Expecting 'name' and 'namespace' to not start with '-' or '_' but '_foo' did
    error_re = r"Invalid collection metadata. Expecting 'name' and 'namespace' to contain alphanumeric characters, "
    "'-', or '_' only but 'foo@blip' contains others"
    error_re = r"Invalid collection metadata. Expecting 'name' and 'namespace' to not start with '-' or '_' but '_foo' did"
    with pytest.raises(ValueError,
                       match=error_re) as exc:
        CollectionInfo(**test_data)
    assert '_foo' in str(exc)


def test_type_list_error():
    test_data = {
        'namespace': 'foo',
        'name': 'foo',
        'authors': 'chouseknecht',
        'license': 'GPL-3.0-or-later',
        'version': '0.0.1',
        'description': 'unit testing thing',
    }
    with pytest.raises(ValueError) as exc:
        CollectionInfo(**test_data)
    assert 'authors' in str(exc)


def test_empty():
    test_data = {}
    # ValueError: Invalid collection metadata. 'namespace' is required
    with pytest.raises(ValueError, match=".*'namespace'.*"):
        CollectionInfo(**test_data)


def test_minimal():
    test_data = {
        'namespace': 'foo',
        'name': 'foo',
        'license': 'GPL-3.0-or-later',
        'version': '1.0.0',
        'description': 'unit testing thing',
    }
    res = CollectionInfo(**test_data)

    res.authors.append('Faux Author')
    res.keywords.append('somekeyword')
    res.dependencies.append(('some_dep', 'stuff'))

    log.debug('res %s res.authors: %s', res, res.authors)

    new_data = test_data.copy()
    res2 = CollectionInfo(**new_data)

    log.debug('res %s res.authors: %s', res, res.authors)
    log.debug('res2 %s res2.authors: %s', res2, res2.authors)

    assert res != res2
    assert res2.authors == []
    assert res2.keywords == []
    assert res2.dependencies == []


def test_authors_append():
    test_data = {
        'namespace': 'foo',
        'name': 'foo',
        # let authors go to the defualt
        # 'authors': ['chouseknecht'],
        'license': 'GPL-3.0-or-later',
        'version': '1.0.0',
        'description': 'unit testing thing',
    }
    res = CollectionInfo(**test_data)
    # log.debug('res %s res.authors: %s', res, res.authors)

    # append to the first objects authors.
    # This should not change the default authors for new
    # CollectionInfo()'s
    res.authors.append('Faux Author')
    log.debug('res %s res.authors: %s', res, res.authors)

    new_data = test_data.copy()

    # No authors provided, should default to []
    res2 = CollectionInfo(**new_data)

    res.authors.append('OnlyAuthoredResNotRes2')

    log.debug('res %s res.authors: %s', res, res.authors)
    log.debug('res2 %s res2.authors: %s', res2, res2.authors)

    # Based on https://www.attrs.org/en/stable/init.html#defaults info about defaults
    # These should not be the same value here
    assert res != res2
    assert res.authors != res2.authors
    assert res2.authors == []
    assert res.authors == ['Faux Author', 'OnlyAuthoredResNotRes2']
    assert 'OnlyAuthoredResNotRes2' not in res2.authors


def test_semantic_version_error():
    test_data = {
        'namespace': 'foo',
        'name': 'foo',
        'authors': ['chouseknecht'],
        'license': 'GPL-3.0-or-later',
        'version': 'foo',
        'description': 'unit testing thing',
    }
    with pytest.raises(ValueError) as exc:
        CollectionInfo(**test_data)
    assert 'version' in str(exc)


def test_namespace_property():
    test_data = {
        'namespace': 'foo',
        'name': 'foo',
        'authors': ['chouseknecht'],
        'license': 'GPL-3.0-or-later',
        'version': '1.0.0',
        'description': 'unit testing thing',
    }
    info = CollectionInfo(**test_data)
    assert info.namespace == 'foo'
