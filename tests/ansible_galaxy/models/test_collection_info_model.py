import logging
import pytest

from ansible_galaxy.models.collection_info import CollectionInfo

log = logging.getLogger(__name__)

NON_ALPHA_ERROR_PAT = r"Invalid collection metadata. Expecting 'name' and 'namespace' to contain only lowercase alphanumeric characters "
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


valid_name_or_namespaces = \
    ['some_name',
     'some_namespace',
     'roles2go',
     'ews',
     'ews_',
     'geerlingguy',
     'red_hat',
     ]


@pytest.fixture(scope='module',
                params=valid_name_or_namespaces)
def valid_name(request):
    yield request.param


def test_valid_names(col_info, valid_name):
    col_info['name'] = valid_name

    log.debug('valid_name: %s', valid_name)

    res = CollectionInfo(**col_info)

    assert isinstance(res, CollectionInfo)
    assert res.name == valid_name


invalid_name_or_namespaces = \
    [
     '2punk__rock--Valid|n a M e s',
     '__builtin__',
     '../../../bin/bash',
     r'\.',
     r'C:\huh\what',
     r'C:\AUX',
     ]


@pytest.fixture(scope='module',
                params=invalid_name_or_namespaces)
def invalid_name(request):
    yield request.param


def test_invalid_names(col_info, invalid_name):
    col_info['name'] = invalid_name

    log.debug('invalid_name: %s', invalid_name)

    with pytest.raises(ValueError) as exc:
        CollectionInfo(**col_info)

    log.debug('exc: %s', str(exc))


invalid_name_leading_underscore = \
    [
        '_scoop_co',
        '__dunder_mifflin',
        '_',
        '_foo',
    ]


@pytest.fixture(scope='module',
                params=invalid_name_leading_underscore)
def invalid_name_leading_underscore(request):
    yield request.param


def test_name_invalid_names_leading_underscore(col_info, invalid_name_leading_underscore):
    col_info['name'] = invalid_name_leading_underscore

    error_re = r"Invalid collection metadata. Expecting 'name' and 'namespace' to not start with '_' but '.*' did"

    log.debug('invalid_name_leading_underscore: %s', invalid_name_leading_underscore)

    with pytest.raises(ValueError,
                       match=error_re) as exc:
        CollectionInfo(**col_info)
    assert invalid_name_leading_underscore in str(exc)


invalid_name_non_alphanumeric = \
    [
     # the '.' in github.com would match the 'no dots' rule first
     'git@github',
     'foo@blip',
     # /, ?, # are non alphanumeric and are invalid
     'rohitggarg/docker-swarm?',
     'c#',
     # leading dash/hyphen and non alpha are invalid
     '--version',
     '-name',
     '-foo',
     # inline '-' is invalid
     'foo-bar',
     'joes-house-of-collections',
     'ansible-galaxy',
     'adfinis-sygroup',
     # double underscores
     'punk__rock',
     'foo__name',
    ]


@pytest.fixture(scope='module',
                params=invalid_name_non_alphanumeric)
def invalid_name_non_alphanumeric(request):
    yield request.param


def test_name_invalid_name_non_alphanumeric(col_info, invalid_name_non_alphanumeric):
    col_info['name'] = invalid_name_non_alphanumeric
    col_info['namespace'] = invalid_name_non_alphanumeric

    log.debug('invalid_name_non_alphanumeric: %s', invalid_name_non_alphanumeric)

    with pytest.raises(ValueError,
                       match=NON_ALPHA_ERROR_PAT) as exc:
        CollectionInfo(**col_info)

    log.debug('exc: %s', str(exc))
    assert invalid_name_non_alphanumeric in str(exc)


def _namespace_invalid_name_non_alphanumeric(col_info, invalid_name_non_alphanumeric):

    log.debug('invalid_name_non_alphanumeric: %s', invalid_name_non_alphanumeric)

    with pytest.raises(ValueError,
                       match=NON_ALPHA_ERROR_PAT) as exc:
        CollectionInfo(**col_info)

    log.debug('exc: %s', str(exc))
    assert invalid_name_non_alphanumeric in str(exc)


invalid_name_leading_number = \
    [
     '0x43',
     '030',
     '2fast2furious',
    ]


@pytest.fixture(scope='module',
                params=invalid_name_leading_number)
def invalid_name_leading_number(request):
    yield request.param


def test_name_invalid_leading_number(col_info, invalid_name_leading_number):
    col_info['name'] = invalid_name_leading_number
    col_info['namespace'] = invalid_name_leading_number

    log.debug('invalid_name_leading_number: %s', invalid_name_leading_number)

    error_re = r"Invalid collection metadata. Expecting 'name' and 'namespace' to not start with a number but '%s' did" % invalid_name_leading_number
    with pytest.raises(ValueError,
                       match=error_re) as exc:
        CollectionInfo(**col_info)
    assert invalid_name_leading_number in str(exc)


invalid_name_uppercase = \
    [
     'EWS',
     'AAROC',
     'AdopteUnOps',
    ]


@pytest.fixture(scope='module',
                params=invalid_name_uppercase)
def invalid_name_uppercase(request):
    yield request.param


def test_name_invalid_uppercase(col_info, invalid_name_uppercase):
    col_info['name'] = invalid_name_uppercase
    col_info['namespace'] = invalid_name_uppercase

    log.debug('invalid_name_uppercase: %s', invalid_name_uppercase)

    with pytest.raises(ValueError,
                       match=NON_ALPHA_ERROR_PAT) as exc:
        CollectionInfo(**col_info)

    log.debug('exc: %s', str(exc))
    assert invalid_name_uppercase in str(exc)


invalid_name_has_dots = \
    [
     'alban.andrieu',
     'dot.net',
     '.',
     '..',
     '_.fsd',
    ]


@pytest.fixture(scope='module',
                params=invalid_name_has_dots)
def invalid_name_has_dots(request):
    yield request.param


def test_name_invalid_has_dots(col_info, invalid_name_has_dots):
    col_info['name'] = invalid_name_has_dots
    col_info['namespace'] = invalid_name_has_dots

    log.debug('invalid_name_has_dots: %s', invalid_name_has_dots)
    error_re = r"Invalid collection metadata. Expecting 'name' and 'namespace' to not include any '\.' but .* has a '\.'"

    with pytest.raises(ValueError,
                       match=error_re) as exc:
        CollectionInfo(**col_info)

    log.debug('exc: %s', str(exc))
    assert invalid_name_has_dots in str(exc)


def test_license_empty_list(col_info):
    col_info['license'] = []

    error_re = r"Valid values for 'license' or 'license_file' are required. But 'license' \(.*\) and 'license_file' \(.*\) were invalid."

    with pytest.raises(ValueError, match=error_re) as exc:
        CollectionInfo(**col_info)

    log.debug('exc: %s', str(exc))


def test_license_valid_and_none_list(col_info):
    col_info['license'] = ['GPL-3.0-or-later', None]

    error_re = r"Invalid collection metadata. Expecting 'license' to be a list of valid SPDX license identifiers, "
    "instead found invalid license identifiers: '.*' in 'license' value .*."

    with pytest.raises(ValueError, match=error_re) as exc:
        CollectionInfo(**col_info)

    log.debug('exc: %s', str(exc))


def test_license_deprecated(col_info):
    col_info['license'] = 'AGPL-1.0'
    res = CollectionInfo(**col_info)
    # Not much to assert, behavior is just a print() side effect
    assert res.license == ['AGPL-1.0']


# TODO maybe... build a text fixture for all of these cases
def test_license_unknown(col_info):
    col_info['license'] = 'SOME-UNKNOWN'
    with pytest.raises(ValueError, match=".*license.*SOME-UNKNOWN.*"):
        CollectionInfo(**col_info)


def test_license_error(col_info):
    col_info['license'] = 'GPLv2'

    with pytest.raises(ValueError) as exc:
        CollectionInfo(**col_info)

    log.debug(str(exc))

    assert 'license' in str(exc)


def test_license_with_valid_license_file(col_info):
    # license=None will be converted to license=[]
    col_info['license'] = None
    col_info['license_file'] = 'MY_LICENSE.txt'

    res = CollectionInfo(**col_info)

    assert res.license_file == 'MY_LICENSE.txt'
    assert res.license == []


def test_license_with_contradicting_license_file(col_info):
    col_info['license_file'] = 'MY_LICENSE.txt'

    res = CollectionInfo(**col_info)

    assert res.license_file == 'MY_LICENSE.txt'
    assert res.license == ['GPL-3.0-or-later']


def test_license_with_none_license_file(col_info):
    col_info['license'] = None
    col_info['license_file'] = None

    error_re = r"Valid values for 'license' or 'license_file' are required. But 'license' \(.*\) and 'license_file' \(.*\) were invalid."
    # error_re = r"Invalid collection metadata. Expecting 'license' to be a list of valid SPDX license identifiers, "
    # "instead found invalid license identifiers: '.*' in 'license' value .*."

    with pytest.raises(ValueError, match=error_re) as exc:
        CollectionInfo(**col_info)

    log.debug('col_info: %s', col_info)
    log.debug(str(exc))


def test_name_required_error(col_info):
    del col_info['name']

    with pytest.raises(ValueError) as exc:
        CollectionInfo(**col_info)
    assert 'name' in str(exc) in str(exc)


def test_namespace_required_error(col_info):
    del col_info['namespace']

    with pytest.raises(ValueError) as exc:
        CollectionInfo(**col_info)
    assert 'namespace' in str(exc) in str(exc)


def test_type_authors_not_list_error(col_info):
    col_info['authors'] = 'chouseknecht'
    with pytest.raises(ValueError) as exc:
        CollectionInfo(**col_info)
    assert 'authors' in str(exc)


def test_tags_non_alpha_error(col_info):
    bad_tag = 'bad-tag!'
    col_info['tags'] = ['goodtag', bad_tag]

    # ValueError: Invalid collection metadata. Expecting tags to contain alphanumeric characters only, instead found 'bad-tag!'.
    error_re = r"Invalid collection metadata. Expecting tags to contain lowercase alphanumeric characters only, instead found '.*'"

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


def test_deps_is_none(col_info):
    col_info['dependencies'] = None
    res = CollectionInfo(**col_info)

    log.debug('res: %s', res)

    assert res.dependencies == {}


def test_deps_is_list(col_info):
    col_info['dependencies'] = ['blip', {'sub_dict': 'these_deps_are_wrong'}]
    error_re = r"Invalid collection metadata. Expecting 'dependencies' to be a dict"

    with pytest.raises(ValueError, match=error_re) as exc:
        CollectionInfo(**col_info)

    log.debug(str(exc))


def test_minimal(col_info):
    del col_info['authors']
    res = CollectionInfo(**col_info)

    res.authors.append('Faux Author')
    res.tags.append('sometag')
    res.dependencies.update({'some_dep': '1.1.0',
                             'stuff': '2.2.2'})

    log.debug('res %s res.authors: %s', res, res.authors)

    new_data = col_info.copy()
    res2 = CollectionInfo(**new_data)

    log.debug('res %s res.authors: %s', res, res.authors)
    log.debug('res2 %s res2.authors: %s', res2, res2.authors)

    assert res != res2
    assert res2.authors == []
    assert res2.tags == []
    assert res2.dependencies == {}


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
