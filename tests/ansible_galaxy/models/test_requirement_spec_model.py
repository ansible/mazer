
import logging

import pytest
import semantic_version

from ansible_galaxy.models import requirement_spec

log = logging.getLogger(__name__)


def test_req_spec():
    rs = requirement_spec.RequirementSpec(namespace='some_ns',
                                          name='some_name',
                                          version_spec='^1.2.3')

    log.debug('rs: %s', rs)
    assert isinstance(rs, requirement_spec.RequirementSpec)
    assert isinstance(rs.version_spec, semantic_version.Spec)

    too_old = semantic_version.Version('1.0.1')
    too_new = semantic_version.Version('3.1.4')
    just_right = semantic_version.Version('1.2.7')

    assert rs.version_spec.match(just_right)
    assert not rs.version_spec.match(too_old)
    assert not rs.version_spec.match(too_new)


def test_from_dict():
    spec_data = {'namespace': 'some_ns',
                 'name': 'some_name',
                 'version_spec': '>1.1.0,!=1.2.2'}

    rs = requirement_spec.RequirementSpec.from_dict(spec_data)

    log.debug('rs: %s', rs)
    assert isinstance(rs, requirement_spec.RequirementSpec)
    assert isinstance(rs.version_spec, semantic_version.Spec)


vspecs_and_expected = \
    [
        {'ver': '1.2.3', 'spec': '==1.2.3', 'expected': True},
        {'ver': '1.2.3', 'spec': '1.2.3', 'expected': True},
        {'ver': '1.2.2', 'spec': '==1.2.3', 'expected': False},
        {'ver': '1.2.3', 'spec': '>=1.2.3', 'expected': True},
        {'ver': '1.2.3', 'spec': '<1.2.3', 'expected': False},
    ]


@pytest.fixture(scope='module',
                params=vspecs_and_expected,
                ids=["spec '%s' matches version '%s' is %s" % (x['spec'], x['ver'], x['expected']) for x in vspecs_and_expected])
def vspecs(request):
    yield request.param


def test_match(vspecs):
    spec_data = {'namespace': 'some_ns',
                 'name': 'some_name',
                 'version_spec': vspecs['spec']}

    rs = requirement_spec.RequirementSpec.from_dict(spec_data)

    log.debug('rs: %s', rs)
    assert isinstance(rs, requirement_spec.RequirementSpec)
    assert isinstance(rs.version_spec, semantic_version.Spec)

    ver = semantic_version.Version(vspecs['ver'])

    assert rs.version_spec.match(ver) == vspecs['expected']
