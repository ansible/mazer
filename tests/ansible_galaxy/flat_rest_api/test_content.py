
import pytest

from ansible_galaxy.flat_rest_api import content


def test_parse_content_name():
    content_name = 'alikins.testing-content'

    user_name, repo_name, content_name = content.parse_content_name(content_name)

    assert user_name == 'alikins'
    assert content_name == 'testing-content'
    assert repo_name is None

    content_name = 'alikins.testing-content.elasticsearch_plugin.py'
    user_name, repo_name, content_name = content.parse_content_name(content_name)

    assert user_name == 'alikins'
    assert content_name == 'elasticsearch_plugin.py'
    assert repo_name == 'testing-content'

    content_name = 'somedotuser.dotuser.testing-content'
    user_name, repo_name, content_name = content.parse_content_name(content_name)

    assert user_name == 'somedotuser.dotuser'
    assert content_name == 'testing-content'
