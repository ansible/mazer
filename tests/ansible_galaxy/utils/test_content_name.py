
from ansible_galaxy.utils import content_name

import logging
log = logging.getLogger(__name__)


def test_parse_content_name():
    _content_name = 'alikins.testing-content'

    user_name, repo_name, _content_name = content_name.parse_content_name(_content_name)

    assert user_name == 'alikins'
    assert _content_name == 'testing-content'
    assert repo_name is None

    _content_name = 'alikins.testing-content.elasticsearch_plugin.py'
    user_name, repo_name, _content_name = content_name.parse_content_name(_content_name)

    assert user_name == 'alikins'
    assert _content_name == 'elasticsearch_plugin.py'
    assert repo_name == 'testing-content'

    # TODO: revisit rules for content name /spec, ie, can
    #       github user ids or namespaces have '.' in them,
    #       and/or can specs for specific contents (a specific module
    #       in a repo) can have a '.' like 'eleastic_search.py'
    # content_name = 'somedotuser.dotuser.testing-content'
    # user_name, repo_name, content_name = content.parse_content_name(content_name)

    # assert user_name == 'somedotuser.dotuser'
    # assert content_name == 'testing-content'
