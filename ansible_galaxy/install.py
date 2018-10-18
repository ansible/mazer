# strategy for installing a Collection (name resolve it, find it,
#  fetch it's artifact, validate/verify it, install/extract it, update install dbs, etc)
# import datetime
import logging
import os
import pprint

import attr

from ansible_galaxy import content_archive
from ansible_galaxy import exceptions
from ansible_galaxy import installed_repository_db
from ansible_galaxy import matchers
from ansible_galaxy.fetch import fetch_factory

log = logging.getLogger(__name__)

# This should probably be a state machine for stepping through the install states
# See actions.install.install_collection for a sketch of the states


def fetcher(galaxy_context, repository_spec):
    log.debug('Attempting to get fetcher for repository_spec=%s', repository_spec)

    fetcher = fetch_factory.get(galaxy_context=galaxy_context,
                                repository_spec=repository_spec)

    log.debug('Using fetcher: %s for repository_spec: %s', fetcher, repository_spec)

    return fetcher


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

#
# The caller of install() may be the best place to figure out things like where to
# extract the content too. Can likely handle figuring out if artifact is a collection_artifact
# or a trad_role_artifact and call different things. Or better, create an approriate
# ArchiveArtifact and just call it's extract()/install() etc.
#
# def install(fetch_results, enough_info_to_figure_out_where_to_extract_etc,
#            probably_a_progress_display_callback, maybe_an_error_callback):
#    pass

    # return install_time? an InstallInfo? list of InstalledCollection?


def update_repository_spec(fetch_results,
                           repository_spec=None):
    '''Verify we got the archive we asked for, checksums, check sigs, etc

    At the moment, also side effect and evols repository_spec to match fetch results
    so that needs to be extracted'''
    # TODO: do we still need to check the fetched version against the spec version?
    #       We do, since the unspecific version is None, so fetched versions wont match
    #       so we need a new repository_spec for install.
    # TODO: this is more or less a verify/validate step or state transition
    content_data = fetch_results.get('content', {})

    # If the requested namespace/version is different than the one we got via find()/fetch()...
    if content_data.get('fetched_version', repository_spec.version) != repository_spec.version:
        log.info('Version "%s" for %s was requested but fetch found version "%s"',
                 repository_spec.version, '%s.%s' % (repository_spec.namespace, repository_spec.name),
                 content_data.get('fetched_version', repository_spec.version))

        repository_spec = attr.evolve(repository_spec, version=content_data['fetched_version'])

    if content_data.get('content_namespace', repository_spec.namespace) != repository_spec.namespace:
        log.info('Namespace "%s" for %s was requested but fetch found namespace "%s"',
                 repository_spec.namespace, '%s.%s' % (repository_spec.namespace, repository_spec.name),
                 content_data.get('content_namespace', repository_spec.namespace))

        repository_spec = attr.evolve(repository_spec, namespace=content_data['content_namespace'])

    return repository_spec


def install(galaxy_context,
            fetcher,
            fetch_results,
            repository_spec,
            force_overwrite=False):
    """extract the archive to the filesystem and write out install metadata.

    MUST be called after self.fetch()."""

    log.debug('install: repository_spec=%s, force_overwrite=%s',
              repository_spec, force_overwrite)
    installed = []

    # FIXME: really need to move the fetch step elsewhere and do it before,
    #        install should get pass a content_archive (or something more abstract)
    # TODO: some useful exceptions for 'cant find', 'cant read', 'cant write'

    archive_path = fetch_results.get('archive_path', None)

    # TODO: this could be pulled up a layer, after getting fetch_results but before install()
    if not archive_path:
        raise exceptions.GalaxyClientError('No valid content data found for...')

    log.debug("installing from %s", archive_path)

    # TODO: this is figuring out the archive type (multi-content collection or a trad role)
    #       could potentially pull this up a layer
    content_archive_ = content_archive.load_archive(archive_path)

    log.debug('content_archive_: %s', content_archive_)
    log.debug('content_archive_.info: %s', content_archive_.info)

    # we strip off any higher-level directories for all of the files contained within
    # the tar file here. The default is 'github_repo-target'. Gerrit instances, on the other
    # hand, does not have a parent directory at all.

    # preparation for archive extraction
    if not os.path.isdir(galaxy_context.content_path):
        log.debug('No content path (%s) found so creating it', galaxy_context.content_path)

        os.makedirs(galaxy_context.content_path)

    # A list of InstallationResults
    res = content_archive_.install(repository_spec=repository_spec,
                                   extract_to_path=galaxy_context.content_path,
                                   force_overwrite=force_overwrite)
    installed.append((repository_spec, res))

    # self.display_callback("- all content was succssfully installed to %s" % self.path)

    # rm any temp files created when getting the content archive
    # TODO: use some sort of callback?
    fetcher.cleanup()

    # TODO: load installed collections back from disk now?
    installed_repository_specs = [x[0] for x in installed]
    log.debug('installed_repository_specs: %s', installed_repository_specs)

    repository_match_filter = matchers.MatchRepositorySpecsNamespaceNameVersion(installed_repository_specs)

    log.debug('repository_match_filter: %s', repository_match_filter)

    icdb = installed_repository_db.InstalledRepositoryDatabase(galaxy_context)
    already_installed_generator = icdb.select(repository_match_filter=repository_match_filter)

    log.debug('already_installed_generator: %s', already_installed_generator)

    installed_repositories = []

    for repository_item in already_installed_generator:
        log.debug('installed repository item: %s', pprint.pformat(repository_item))

        # TODO: InstallationResults object
        installed_repository_spec = repository_item.repository_spec
        # installation_results = item[1]
        path = repository_item.path

        log.info('Installed repository repository_spec: %s', installed_repository_spec)
        log.info('installed repository path: %s', path)

        all_deps = repository_item.requirements or []
        all_deps.extend(repository_item.dependencies or [])

        installed_repositories.append(repository_item)

    log.debug('installed_repositories: %s', pprint.pformat(installed_repositories))

    return installed_repositories
