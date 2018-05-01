import logging
import pytest

from ansible_galaxy.flat_rest_api import content

log = logging.getLogger(__name__)


def test_yaml_parse():
    content_str = 'git+https://github.com/atestuseraccount/ansible-testing-content.git,1.2.3'
    ret = content.GalaxyContent.yaml_parse(content_str)

    log.debug('content_str: %s ret: %s', content_str, ret)

    assert ret['name'] == 'ansible-testing-content'
    assert ret['version'] == '1.2.3'

    content_str = 'git+https://github.com/atestuseraccount/ansible-testing-content.git,name=elasticsearch_plugin.py'
    ret = content.GalaxyContent.yaml_parse(content_str)

    log.debug('content_str: %s ret: %s', content_str, ret)

    assert ret['name'] == 'ansible-testing-content'
    assert ret['version'] == 'asdfsdf'



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
