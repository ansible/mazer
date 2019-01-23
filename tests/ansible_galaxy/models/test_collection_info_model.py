import logging
import pytest

from ansible_galaxy.models.collection_info import CollectionInfo

log = logging.getLogger(__name__)

NON_ALPHA_ERROR_PAT = r"Invalid collection metadata. Expecting 'name' and 'namespace' to contain only alphanumeric characters "
"or '_' only but '.*' contains others"


@pytest.fixture
def col_info():
    test_data = {
        'namespace': 'foo',
        'name': 'foo',
        'authors': ['chouseknecht'],
        'license': 'GPL-3.0-or-later',
        'version': '0.0.1',
        'description': 'unit testing thing',
    }
    return test_data


def test_license_deprecated(col_info):
    col_info['license'] = 'AGPL-1.0'
    res = CollectionInfo(**col_info)
    # Not much to assert, behavior is just a print() side effect
    assert res.license == 'AGPL-1.0'


def test_license_unknown(col_info):
    col_info['license'] = 'SOME-UNKNOWN'
    with pytest.raises(ValueError, match=".*license.*SOME-UNKNOWN.*"):
        CollectionInfo(**col_info)


def test_license_error(col_info):
    col_info['license'] = 'GPLv2'

    with pytest.raises(ValueError) as exc:
        CollectionInfo(**col_info)
    assert 'license' in str(exc)


def test_name_required_error(col_info):
    del col_info['name']

    with pytest.raises(ValueError) as exc:
        CollectionInfo(**col_info)
    assert 'name' in str(exc) in str(exc)


def test_name_parse_error_dots_in_name(col_info):
    col_info['name'] = 'foo.bar'

    # CollectionInfo(**col_info)
    # ValueError: Invalid collection metadata. Expecting 'name' and 'namespace' to not include any '.' but 'foo.bar' has a '.'
    error_re = r"Invalid collection metadata. Expecting 'name' and 'namespace' to not include any '\.' but 'foo\.bar' has a '\.'"
    with pytest.raises(ValueError,
                       match=error_re) as exc:
        CollectionInfo(**col_info)
    assert 'name' in str(exc)


def test_name_parse_error_other_chars_namespace(col_info):
    col_info['namespace'] = 'foo@blip'

    # ValueError: Invalid collection metadata. Expecting 'name' and 'namespace' to contain only alphanumeric characters
    # or '_' only but 'foo@blip' contains others"
    with pytest.raises(ValueError,
                       match=NON_ALPHA_ERROR_PAT) as exc:
        CollectionInfo(**col_info)
    assert 'foo@blip' in str(exc)


def test_name_parse_error_name_leading_underscore(col_info):
    col_info['name'] = '_foo'

    # ValueError: Invalid collection metadata. Expecting 'name' and 'namespace' to not start with '_' but '_foo' did
    error_re = r"Invalid collection metadata. Expecting 'name' and 'namespace' to not start with '_' but '_foo' did"
    with pytest.raises(ValueError,
                       match=error_re) as exc:
        CollectionInfo(**col_info)
    assert '_foo' in str(exc)


def test_name_parse_error_name_leading_hyphen(col_info):
    col_info['name'] = '-foo'

    # For the case of a leading '-', the 'no dashes' check raises error first
    with pytest.raises(ValueError,
                       match=NON_ALPHA_ERROR_PAT) as exc:
        CollectionInfo(**col_info)
    assert '-foo' in str(exc)


def test_name_has_hypen_error(col_info):
    col_info['name'] = 'foo-bar'

    with pytest.raises(ValueError,
                       match=NON_ALPHA_ERROR_PAT) as exc:
        CollectionInfo(**col_info)
    assert 'foo-bar' in str(exc)


def test_namespace_has_hypen_error(col_info):
    col_info['namespace'] = 'foo-namespace'

    with pytest.raises(ValueError,
                       match=NON_ALPHA_ERROR_PAT) as exc:
        CollectionInfo(**col_info)
    assert 'foo-namespace' in str(exc)


def test_type_authors_not_list_error(col_info):
    col_info['authors'] = 'chouseknecht'
    with pytest.raises(ValueError) as exc:
        CollectionInfo(**col_info)
    assert 'authors' in str(exc)


def test_tags_non_alpha_error(col_info):
    bad_tag = 'bad-tag!'
    col_info['tags'] = ['goodtag', bad_tag]

    # ValueError: Invalid collection metadata. Expecting tags to contain alphanumeric characters only, instead found 'bad-tag!'.
    error_re = r"Invalid collection metadata. Expecting tags to contain alphanumeric characters only, instead found '.*'"

    with pytest.raises(ValueError,
                       match=error_re) as exc:
        CollectionInfo(**col_info)
    assert bad_tag in str(exc)


def test_tags_not_a_list_error(col_info):
    not_a_list = 'notataglist'
    col_info['tags'] = not_a_list

    # ValueError: Invalid collection metadata. Expecting 'tags' to be a list
    error_re = r"Invalid collection metadata. Expecting 'tags' to be a list"

    with pytest.raises(ValueError,
                       match=error_re) as exc:
        CollectionInfo(**col_info)
    assert 'tags' in str(exc)


def test_empty():
    col_info = {}
    # ValueError: Invalid collection metadata. 'namespace' is required
    with pytest.raises(ValueError, match=".*'namespace'.*"):
        CollectionInfo(**col_info)


def test_minimal(col_info):
    del col_info['authors']
    res = CollectionInfo(**col_info)

    res.authors.append('Faux Author')
    res.tags.append('sometag')
    res.dependencies.append(('some_dep', 'stuff'))

    log.debug('res %s res.authors: %s', res, res.authors)

    new_data = col_info.copy()
    res2 = CollectionInfo(**new_data)

    log.debug('res %s res.authors: %s', res, res.authors)
    log.debug('res2 %s res2.authors: %s', res2, res2.authors)

    assert res != res2
    assert res2.authors == []
    assert res2.tags == []
    assert res2.dependencies == []


def test_authors_append(col_info):
    # let authors go to the defualt
    del col_info['authors']
    res = CollectionInfo(**col_info)
    # log.debug('res %s res.authors: %s', res, res.authors)

    # append to the first objects authors.
    # This should not change the default authors for new
    # CollectionInfo()'s
    res.authors.append('Faux Author')
    log.debug('res %s res.authors: %s', res, res.authors)

    new_data = col_info.copy()

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


def test_semantic_version_error(col_info):
    col_info['version'] = 'notaversion'
    with pytest.raises(ValueError) as exc:
        CollectionInfo(**col_info)
    assert 'version' in str(exc)


def test_namespace_property(col_info):
    info = CollectionInfo(**col_info)
    assert info.namespace == 'foo'


def test_label_property(col_info):
    info = CollectionInfo(**col_info)
    assert info.label == 'foo.foo'
