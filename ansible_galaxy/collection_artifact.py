import logging

import attr

from ansible_galaxy import exceptions
from ansible_galaxy import repository
from ansible_galaxy import repository_archive
from ansible_galaxy.utils import chksums

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


def validate_artifact(artifact_path, expected_chksum):
    '''Check the sha256sum of file at `artifact_path` against `expected_chksum`

    Raise a GalaxyArtifactChksumError if they don't match.
    '''
    actual = chksums.sha256sum_from_path(artifact_path)

    if actual != expected_chksum:
        raise exceptions.GalaxyArtifactChksumError(artifact_path=artifact_path,
                                                   expected=expected_chksum,
                                                   actual=actual)
