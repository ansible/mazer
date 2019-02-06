import logging

from ansible_galaxy.models import repository_spec
from ansible_galaxy.models import requirement
from ansible_galaxy.models import requirement_spec

log = logging.getLogger(__name__)


def test_requirement_op():
    ops = requirement.RequirementOps()
    assert isinstance(ops, requirement.RequirementOps)
    assert ops.EQ == '='


def test_requirement():
    repo_spec1 = repository_spec.RepositorySpec(namespace='mynamespace',
                                                name='myname',
                                                version='3.4.5')

    provides_spec2 = requirement_spec.RequirementSpec(namespace='othernamespace',
                                                      name='provides_something',
                                                      version_spec='==1.0.0')

    req = requirement.Requirement(repository_spec=repo_spec1, requirement_spec=provides_spec2,
                                  op=requirement.RequirementOps.EQ)

    assert isinstance(req, requirement.Requirement)
    assert req.repository_spec == repo_spec1
    assert req.requirement_spec == provides_spec2


def test_repository_spec_requirement_spec_cmp():
    repo_spec1 = repository_spec.RepositorySpec(namespace='ns',
                                                name='n',
                                                version='3.4.5')

    req_spec = requirement_spec.RequirementSpec(namespace='ns',
                                                name='n',
                                                version_spec='==3.4.5')

    req = requirement.Requirement(repository_spec=repo_spec1, requirement_spec=req_spec,
                                  op=requirement.RequirementOps.EQ)

    log.debug('req: %s', req)
    log.debug('repo_spec1: %s', repo_spec1)
    log.debug('req_spec: %s', req_spec)

    assert req.repository_spec == repo_spec1
    assert req.requirement_spec == req_spec
