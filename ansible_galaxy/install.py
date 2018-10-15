# strategy for installing a Collection (name resolve it, find it,
#  fetch it's artifact, validate/verify it, install/extract it, update install dbs, etc)
# import datetime
import logging
import os
import pprint

import attr

from ansible_galaxy import content_archive
from ansible_galaxy import exceptions
from ansible_galaxy import installed_collection_db
from ansible_galaxy import matchers
from ansible_galaxy.fetch import fetch_factory
# from ansible_galaxy import install_info
# from ansible_galaxy.models.install_info import InstallInfo
from ansible_galaxy.models.content import InstalledContent

# FIXME: remove
# from ansible_galaxy.flat_rest_api.content import InstalledContent

log = logging.getLogger(__name__)

# This should probably be a state machine for stepping through the install states
# See actions.install.install_collection for a sketch of the states
#
# But... we are going to start with just extracting the related bits of
# flat_rest_api.content.GalaxyContent here as methods

# def find
# def fetch
# def install
# def update_dbs


def fetcher(galaxy_context, content_spec):
    log.debug('Attempting to get fetcher for content_spec=%s', content_spec)

    fetcher = fetch_factory.get(galaxy_context=galaxy_context,
                                content_spec=content_spec)

    log.debug('Using fetcher: %s for content_spec: %s', fetcher, content_spec)

    return fetcher


def find(fetcher, content_spec):
    """find/discover info about the content"""

    log.debug('Attempting to find() content_spec=%s', content_spec)

    find_results = fetcher.find()

    # log.debug('find() found info for %s: %s', content_spec.label, find_results)

    return find_results


# def fetch(fetcher, collection):
#    pass

def fetch(fetcher, content_spec, find_results):
    """download the archive and side effect set self._archive_path to where it was downloaded to.

    MUST be called after self.find()."""

    log.debug('Fetching content_spec=%s', content_spec)

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


def update_content_spec(fetch_results,
                        content_spec=None,
                        # content_meta=None,
                        ):
    '''Verify we got the archive we asked for, checksums, check sigs, etc

    At the moment, also side effect and evols content_spec to match fetch results
    so that needs to be extracted'''
    # TODO: do we still need to check the fetched version against the spec version?
    #       We do, since the unspecific version is None, so fetched versions wont match
    #       so we need a new content_spec for install.
    # TODO: this is more or less a verify/validate step or state transition
    content_data = fetch_results.get('content', {})

    # If the requested namespace/version is different than the one we got via find()/fetch()...
    if content_data.get('fetched_version', content_spec.version) != content_spec.version:
        log.info('Version "%s" for %s was requested but fetch found version "%s"',
                 content_spec.version, '%s.%s' % (content_spec.namespace, content_spec.name),
                 content_data.get('fetched_version', content_spec.version))

        content_spec = attr.evolve(content_spec, version=content_data['fetched_version'])

    if content_data.get('content_namespace', content_spec.namespace) != content_spec.namespace:
        log.info('Namespace "%s" for %s was requested but fetch found namespace "%s"',
                 content_spec.namespace, '%s.%s' % (content_spec.namespace, content_spec.name),
                 content_data.get('content_namespace', content_spec.namespace))

        content_spec = attr.evolve(content_spec, namespace=content_data['content_namespace'])

    return content_spec


def install(galaxy_context,
            fetcher,
            fetch_results,
            content_spec,
            # content_meta=None,
            force_overwrite=False):
    """extract the archive to the filesystem and write out install metadata.

    MUST be called after self.fetch()."""

    log.debug('install: content_spec=%s, force_overwrite=%s',
              content_spec, force_overwrite)
    installed = []

    # FIXME: enum/constant/etc demagic
    # content_archive_type = 'multi'

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
    # TODO: content_tar_file and archive_meta probably should be attributes of of
    #       InstallableArchive (somewhere between GalaxyContent, GalaxyContentMeta,
    #       ContentArchiveMeta...)
    # content_tar_file, archive_meta = content_archive.load_archive(archive_path)
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

    # FIXME: guess might as well pass in content_spec
    res = content_archive_.install(content_spec=content_spec,
                                   # content_namespace=content_spec.namespace,
                                   # content_name=content_spec.name,
                                   # content_version=content_spec.version,
                                   # surely wrong...
                                   extract_to_path=galaxy_context.content_path,
                                   force_overwrite=force_overwrite)
    installed.append((content_spec, res))

    # self.display_callback("- all content was succssfully installed to %s" % self.path)

    # rm any temp files created when getting the content archive
    # TODO: use some sort of callback?
    fetcher.cleanup()

    # TODO: load installed collections back from disk now?
    installed_content_specs = [x[0] for x in installed]
    log.debug('installed_content_specs: %s', installed_content_specs)

    collection_match_filter = matchers.MatchContentSpecsNamespaceNameVersion(installed_content_specs)

    log.debug('collectio_match_filter: %s', collection_match_filter)

    icdb = installed_collection_db.InstalledCollectionDatabase(galaxy_context)
    already_installed_generator = icdb.select(collection_match_filter=collection_match_filter)

    log.debug('already_installed_generator: %s', already_installed_generator)

    installed_contents = []

    # log.debug('FOOO: %s', [x for x in already_installed_generator])
    for collection_item in already_installed_generator:
        log.debug('installed collection item: %s', pprint.pformat(collection_item))

        # TODO: InstallationResults object
        installed_content_spec = collection_item.content_spec
        # installation_results = item[1]
        path = collection_item.path

        log.info('Installed collection content_spec: %s', installed_content_spec)
        log.info('installed collection path: %s', path)
        # log.info('Installation results: %s', pprint.pformat(attr.asdict(installation_results)))
        #  name=test-role-c, namespace=alikins, path=/home/adrian/.ansible/content/alikins/ansible_testing_content/roles/test-role-c

        # TODO: Replace with InstalledCollection ?
        # FIXME:

        all_deps = collection_item.requirements or []
        all_deps.extend(collection_item.dependencies or [])

        installed_content = InstalledContent(name=installed_content_spec.name,
                                             namespace=installed_content_spec.namespace,
                                             version=installed_content_spec.version,
                                             # dependencies=collection_item.dependencies,
                                             requirements=all_deps,
                                             # install_info=installation_results.install_info,
                                             # meta_main=installation_results.meta_main,
                                             # content_type=installed_content_spec.content_type,
                                             # TESTME:
                                             # path=content_meta.path,
                                             # path=repo_install_path,
                                             )
        installed_contents.append(installed_content)
        # log.debug('Installed files: %s', pprint.pformat(item[1]))

    log.debug('installed_contents: %s', pprint.pformat(installed_contents))
    return installed_contents
