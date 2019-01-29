import logging

import attr

from ansible_galaxy import repository
from ansible_galaxy import repository_archive

log = logging.getLogger(__name__)


def load_data_from_collection_artifact(repository_spec_string):
    log.debug('repo_spec_string: %s', repository_spec_string)

    # TODO: may need some name/path sanitations here
    archive_file_name = repository_spec_string

    repo_archive = repository_archive.load_archive(archive_file_name,
                                                   repository_spec=None)

    log.debug('repo_archive: %s', repo_archive)

    repo = repository.load_from_archive(repo_archive)

    # TODO: asdict?
    spec_data = repo.repository_spec
    log.debug('spec_data: %s', spec_data)

    # FIXME: we already have a valid RepositorySpec, but we dict'ify it here
    #        so existing code that assumes a dict continues to work
    return attr.asdict(spec_data)
