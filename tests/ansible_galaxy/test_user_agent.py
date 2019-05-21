import logging
import sys

import ansible_galaxy
from ansible_galaxy import user_agent

log = logging.getLogger(__name__)


def test_user_agent():
    res = user_agent.user_agent()
    assert res.startswith('Mazer/%s' % ansible_galaxy.__version__)
    assert sys.platform in res
    assert 'python:' in res
    assert 'ansible_galaxy' in res
