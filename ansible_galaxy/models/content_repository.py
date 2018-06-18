import logging

import yaml

log = logging.getLogger(__name__)

# The galaxy_metadata will contain a dict that defines
# a section for each content type to be installed
# and then a list of types with their deps and src
#
# FIXME - Link to permanent public spec once it exists
#
# https://github.com/ansible/galaxy/issues/245
# https://etherpad.net/p/Galaxy_Metadata
#
# Example to install modules with module_utils deps:
########
# meta_version: '0.1'  #metadata format version
# modules:
# - path: playbooks/modules/*
# - path: modules/module_b
#   dependencies:
#     - src: /module_utils
# - path: modules/module_c.py
#   dependencies:
#     - src: namespace.repo_name.module_name
#       type: module_utils
#     - src: ssh://git@github.com/acme/ansible-example.git
#       type: module_utils
#       version: master
#       scm: git
#       path: common/utils/*
# - src: namespace.repo_name.plugin_name
#       type: action_plugin
#######
#
#
# Handle "modules" for MVP, add more types later
#
# A more generic way would be to do this, but we're
# not "there yet"
#   if content == self.type_dir:
#
#   self.galaxy_metadata[content] # General processing


def load(data_or_file_object):
    content_repository = yaml.safe_load(data_or_file_object)
    return content_repository


class ContentRepository(object):
    def __init__(self,
                 namespace=None,
                 name=None,
                 path=None):
        self.namespace = namespace
        self.name = name
        self.path = path

    @classmethod
    def from_content_spec_data(cls, content_spec_data):
        return cls(namespace=content_spec_data.get('namespace'),
                   name=content_spec_data.get('name'))

    def __repr__(self):
        return '%s(namespace="%s", name="%s", path="%s")' % \
            (self.__class__.__name__, self.namespace,
             self.name, self.path)
