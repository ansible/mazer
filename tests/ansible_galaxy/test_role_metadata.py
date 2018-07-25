import io
import logging

from ansible_galaxy import role_metadata
from ansible_galaxy.models.role_metadata import RoleMetadata

log = logging.getLogger(__name__)

yaml_data1 = u'''
---
dependencies: []

galaxy_info:
  author: geerlingguy
  description: Apache 2.x for Linux.
  company: "Midwestern Mac, LLC"
  license: "license (BSD, MIT)"
  min_ansible_version: 2.2
  platforms:
    - name: EL
      versions:
        - all
    - name: Amazon
      versions:
        - all
    - name: Debian
      versions:
        - all
    - name: Ubuntu
      versions:
        - precise
        - raring
        - saucy
        - trusty
        - xenial
    - name: Suse
      versions:
        - all
    - name: Solaris
      versions:
        - 11.3
  galaxy_tags:
    - web
    - apache
    - webserver
    - html

allow_duplicates: yes
'''


def test_load():
    yaml_fo = io.StringIO(initial_value=yaml_data1)
    role_md = role_metadata.load(yaml_fo, role_name='apache')

    assert isinstance(role_md, RoleMetadata)

    assert role_md.name == 'apache'
    assert role_md.min_ansible_version == '2.2'
    assert isinstance(role_md.galaxy_tags, list)
    assert 'web' in role_md.galaxy_tags
    assert role_md.galaxy_tags == ['web', 'apache', 'webserver', 'html']
    assert isinstance(role_md.allow_duplicates, bool)


def test_load_string():
    role_md = role_metadata.load(yaml_data1, role_name='apache')

    log.debug('role_md: %s', role_md)

    assert isinstance(role_md, RoleMetadata)
    assert role_md.name == 'apache'
    assert role_md.min_ansible_version == '2.2'
    assert isinstance(role_md.galaxy_tags, list)
    assert 'web' in role_md.galaxy_tags
    assert role_md.galaxy_tags == ['web', 'apache', 'webserver', 'html']
    assert isinstance(role_md.allow_duplicates, bool)
