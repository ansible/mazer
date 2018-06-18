import logging
import pytest

from ansible_galaxy import matchers
from ansible_galaxy.models.content_repository import ContentRepository

log = logging.getLogger(__name__)

CR = ContentRepository


@pytest.mark.parametrize("matcher_class,matcher_args,candidates, expected", [
    (matchers.MatchAll, tuple(), [1], True),
    (matchers.MatchAll, tuple(), ['a', 'b', 3],  True),
    (matchers.MatchNone, tuple(), ['a', 'b', 3],  False),
    (matchers.MatchNames, (['name1', 'name2'], ), [CR(name='name1')], True),
    (matchers.MatchNames, (['name1', 'name2'], ), [CR(name='blargh')], False),
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

        log.debug('res: %s, candidate=%s, expected=%s', res, candidate, expected)
        assert res is expected, 'res %s for candidate=%s was not %s' % (res, candidate, expected)
