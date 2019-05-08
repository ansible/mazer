# strategy for installing a Collection (name resolve it, find it,
#  fetch it's artifact, validate/verify it, install/extract it, update install dbs, etc)
import logging
import os
import pprint

import attr

from ansible_galaxy import repository_archive
from ansible_galaxy import exceptions
from ansible_galaxy import installed_repository_db
from ansible_galaxy.models.install_destination import InstallDestinationInfo
from ansible_galaxy.models.repository_spec import FetchMethods, RepositorySpec

log = logging.getLogger(__name__)

# This should probably be a state machine for stepping through the install states
# See actions.install.install_collection for a sketch of the states


def find(fetcher):
    """find/discover info about the content"""

    find_results = fetcher.find()

    return find_results


# def fetch(fetcher, collection):
#    pass

def fetch(fetcher, repository_spec, find_results):
    """download the archive and side effect set self._archive_path to where it was downloaded to.

    MUST be called after self.find()."""

    log.debug('Fetching repository_spec=%s', repository_spec)

    try:
        # FIXME: note that ignore_certs for the galaxy
        # server(galaxy_context.server['ignore_certs'])
        # does not really imply that the repo archive download should ignore certs as well
        # (galaxy api server vs cdn) but for now, we use the value for both
        fetch_results = fetcher.fetch(find_results=find_results)
    except exceptions.GalaxyDownloadError as e:
        log.exception(e)

        # TODO: having to keep fetcher state for tracking fetcher.remote_resource and/or cleanup
        #       is kind of annoying.These methods may need to be in a class. Or maybe
        #       the GalaxyDownloadError shoud/could have any info.
        blurb = 'Failed to fetch the content archive "%s": %s'
        log.error(blurb, fetcher.remote_resource, e)

        # reraise, currently handled in main
        # TODO: if we support more than one archive per invocation, will need to accumulate errors
        #       if we want to skip some of them
        raise

    return fetch_results


def repository_spec_from_find_results(find_results,
                                      requirement_spec):
    '''Create a new RepositorySpec with updated info from fetch_results.

    Evolves repository_spec to match fetch results.'''

    # TODO: do we still need to check the fetched version against the spec version?
    #       We do, since the unspecific version is None, so fetched versions wont match
    #       so we need a new repository_spec for install.
    # TODO: this is more or less a verify/validate step or state transition
    content_data = find_results.get('content', {})
    resolved_version = content_data.get('version')

    log.debug('version_spec "%s" for %s was requested and was resolved to version "%s"',
              requirement_spec.version_spec, requirement_spec.label,
              resolved_version)

    # In theory, a fetch can return a different namespace/name than the one request. This
    # is for things like server side aliases.
    resolved_name = content_data.get('fetched_name', requirement_spec.name)
    resolved_namespace = content_data.get('content_namespace', requirement_spec.namespace)

    # Build a RepositorySpec based on RequirementSpec and the extra info resolved in find()
    spec_data = attr.asdict(requirement_spec)

    del spec_data['version_spec']

    spec_data['version'] = resolved_version
    spec_data['namespace'] = resolved_namespace
    spec_data['name'] = resolved_name

    repository_spec = RepositorySpec.from_dict(spec_data)
    return repository_spec


def install(galaxy_context,
            fetcher,
            fetch_results,
            repository_spec,
            force_overwrite=False,
            display_callback=None):
    """extract the archive to the filesystem and write out install metadata.

    MUST be called after self.fetch()."""

    log.debug('install: repository_spec=%s, force_overwrite=%s',
              repository_spec, force_overwrite)
    just_installed_spec_and_results = []

    # FIXME: really need to move the fetch step elsewhere and do it before,
    #        install should get pass a content_archive (or something more abstract)
    # TODO: some useful exceptions for 'cant find', 'cant read', 'cant write'

    archive_path = fetch_results.get('archive_path', None)

    # TODO: this could be pulled up a layer, after getting fetch_results but before install()
    if not archive_path:
        raise exceptions.GalaxyClientError('No valid content data found for...')

    log.debug("installing from %s", archive_path)

    repo_archive_ = repository_archive.load_archive(archive_path, repository_spec)

    log.debug('repo_archive_: %s', repo_archive_)
    log.debug('repo_archive_.info: %s', repo_archive_.info)

    # we strip off any higher-level directories for all of the files contained within
    # the tar file here. The default is 'github_repo-target'. Gerrit instances, on the other
    # hand, does not have a parent directory at all.

    # preparation for archive extraction
    if not os.path.isdir(galaxy_context.collections_path):
        log.debug('No content path (%s) found so creating it', galaxy_context.collections_path)

        os.makedirs(galaxy_context.collections_path)

    # Build up all the info about where the repository will be installed to
    namespaced_repository_path = '%s/%s' % (repository_spec.namespace,
                                            repository_spec.name)

    editable = repository_spec.fetch_method == FetchMethods.EDITABLE

    destination_info = InstallDestinationInfo(collections_path=galaxy_context.collections_path,
                                              repository_spec=repository_spec,
                                              namespaced_repository_path=namespaced_repository_path,
                                              force_overwrite=force_overwrite,
                                              editable=editable)

    # A list of InstallationResults
    res = repository_archive.install(repo_archive_,
                                     repository_spec=repository_spec,
                                     destination_info=destination_info,
                                     display_callback=display_callback)

    just_installed_spec_and_results.append((repository_spec, res))

    if display_callback:
        display_callback("- The repository %s was successfully installed to %s" % (repository_spec.label,
                                                                                   galaxy_context.collections_path))

    # rm any temp files created when getting the content archive
    # TODO: use some sort of callback?
    fetcher.cleanup()

    # We know the repo specs for the repos we asked to install, and the installation results,
    # so now use that info to find the just installed repos on disk and load them and return them.
    just_installed_repository_specs = [x[0] for x in just_installed_spec_and_results]

    # log.debug('just_installed_repository_specs: %s', just_installed_repository_specs)

    irdb = installed_repository_db.InstalledRepositoryDatabase(galaxy_context)

    just_installed_repositories = []

    for just_installed_repository_spec in just_installed_repository_specs:
        just_installed_repository_gen = irdb.by_repository_spec(just_installed_repository_spec)

        # TODO: Eventually, we could make install.install return a generator and yield these results straigt
        #       from just_installed_repository_generator. The loop here is mostly for logging/feedback.
        # Should only get one answer here for now.
        for just_installed_repository in just_installed_repository_gen:
            log.debug('just_installed_repository is installed: %s', pprint.pformat(attr.asdict(just_installed_repository)))

            just_installed_repositories.append(just_installed_repository)

    # log.debug('just_installed_repositories: %s', pprint.pformat(just_installed_repositories))

    return just_installed_repositories
