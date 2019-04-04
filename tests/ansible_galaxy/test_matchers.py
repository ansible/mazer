import logging
import pytest

from ansible_galaxy import matchers
from ansible_galaxy.models.repository import Repository
from ansible_galaxy.models.repository_spec import RepositorySpec

log = logging.getLogger(__name__)


def CR(namespace=None, name=None):
    cs = RepositorySpec(namespace=namespace,
                        name=name,
                        version='1.2.3')
    return Repository(repository_spec=cs)


@pytest.mark.parametrize("matcher_class,matcher_args,candidates, expected", [
    (matchers.MatchAll, tuple(), [1], True),
    (matchers.MatchAll, tuple(), ['a', 'b', 3],  True),
    (matchers.MatchNone, tuple(), ['a', 'b', 3],  False),
    (matchers.MatchLabels,
     (['ns1.name1'], ),
     [CR(namespace='ns1', name='name1')],
     True),
    (matchers.MatchLabels,
     (['ns1.name1'], ),
     [CR(namespace='ns1', name='name2')],
     False),
    (matchers.MatchLabels,
     (['ns1.name1'], ),
     [CR(namespace='ns2', name='name1')],
     False),
    (matchers.MatchLabels,
     (['ns1.name1'], ),
     [CR(namespace='ns2', name='name2')],
     False),
    (matchers.MatchNamespacesOrLabels,
     (['ns1', 'offlabel'],),
     [CR(namespace='ns1')],
     True),
    (matchers.MatchNamespacesOrLabels,
     (['ns1', 'offlabel'],),
     [CR(namespace='ns1', name='name1')],
     True),
    (matchers.MatchNamespacesOrLabels,
     (['ns1.name1'],),
     [CR(namespace='ns1', name='name1')],
     True),
    (matchers.MatchNamespacesOrLabels,
     (['ns1.name1'],),
     [CR(namespace='ns1', name='name2')],
     False),
    (matchers.MatchNamespacesOrLabels,
     (['ns1.name1'],),
     [CR(namespace='ns2', name='name1')],
     False),
    (matchers.MatchNamespacesOrLabels,
     (['ns2.name2'],),
     [CR(namespace='ns1', name='name1')],
     False)

])
def test_match_all(matcher_class, matcher_args, candidates, expected):
    log.debug('matcher_class=%s matcher_args=%s candidate=%s, expected=%s', matcher_class, matcher_args, candidates, expected)

    matcher = matcher_class(*matcher_args)
    for candidate in candidates:
        res = matcher(candidate)

        log.debug('res: %s, matcher=%s, candidate=%s, expected=%s', res, matcher, candidate, expected)
        assert res is expected, 'res %s for matcher=%s candidate=%s was not %s' % (res, matcher, candidate, expected)
