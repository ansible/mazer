import logging
import os

import attr

from ansible_galaxy.config.defaults import COLLECTIONS_PYTHON_NAMESPACE
from ansible_galaxy.models.repository_spec import RepositorySpec

log = logging.getLogger(__name__)

INSTALL_RECORD = '.galaxy_install_info'


@attr.s(frozen=True)
class InstallDestinationInfo(object):
    collections_path = attr.ib()

    repository_spec = attr.ib(type=RepositorySpec)

    # For example 'alikins/collections_reqs_test/'
    namespaced_repository_path = attr.ib()

    force_overwrite = attr.ib(default=False)

    editable = attr.ib(default=False)

    python_namespace = attr.ib(default=COLLECTIONS_PYTHON_NAMESPACE)

    @property
    def path(self):
        '''The full path to the eventually installed repository

        For, /home/user/.ansible/collections/ansible_collections/geerlingguy/ntp
        '''
        return os.path.join(self.collections_path,
                            self.python_namespace,
                            self.namespaced_repository_path)

    @property
    def install_info_path(self):
        '''The full path to the eventually installed collections install record

        For, /home/user/.ansible/collections/ansible_collections/geerlingguy/ntp/meta/.galaxy_install_info
        '''
        return os.path.join(self.path, 'meta', INSTALL_RECORD)
