import logging
import shutil

import yaml

import attr

from ansible_galaxy.models import repository_namespace

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


# TODO/FIXME: mv out of models/ to ansible_galaxy/content_repository
def load(data_or_file_object):
    content_repository = yaml.safe_load(data_or_file_object)
    return content_repository


def remove(installed_repository):
    log.info("Removing installed repository: %s", installed_repository)
    try:
        shutil.rmtree(installed_repository.path)
        return True
    except EnvironmentError as e:
        log.warn('Unable to rm the directory "%s" while removing installed repo "%s": %s',
                 installed_repository.path,
                 installed_repository.label,
                 e)
        log.exception(e)
        raise


@attr.s
class ContentRepository(object):
    namespace = attr.ib()
    name = attr.ib()
    path = attr.ib(default=None)
    label = attr.ib(default=None)

    @property
    def label(self):
        return '%s.%s' % (self.namespace.namespace, self.name)
