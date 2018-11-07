import logging
import os

import attr

from ansible_galaxy.models.repository_spec import RepositorySpec

log = logging.getLogger(__name__)


@attr.s(frozen=True)
class InstallDestinationInfo(object):
    destination_root_dir = attr.ib()
    repository_spec = attr.ib(type=RepositorySpec)

    # NOTE: destination_root_dir is the root of where the install begins
    #       but extract_archive_to is where the archive is extract to.
    #       The normal case (collection or multi-content archives) these values
    #       are the same (for ex, ~/.ansible/content/alikins/some_collection), but
    #       for trad roles they are different (for ex,
    #       destination_root_dir=~/.ansible/content/geerlingguy/ntp when
    #       extract_archive_to_dir=~/.ansible/content/geerlingguy/ntp/roles/ntp)
    extract_archive_to_dir = attr.ib()

    # 'alikins/collections_reqs_test/'
    namespaced_repository_path = attr.ib()

    install_info_path = attr.ib()

    force_overwrite = attr.ib(default=False)

    editable = attr.ib(default=False)

    @property
    def path(self):
        '''The full path to the eventually installed repository

        For, /home/user/.ansible/content/geerlingguy/ntp
        '''
        return os.path.join(self.destination_root_dir,
                            self.namespaced_repository_path)
