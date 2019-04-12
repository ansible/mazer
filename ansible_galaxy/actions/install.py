import logging
import pprint

from ansible_galaxy import collection_artifact
from ansible_galaxy import display
from ansible_galaxy import download
from ansible_galaxy import exceptions
from ansible_galaxy import install
from ansible_galaxy import installed_repository_db
from ansible_galaxy import matchers
from ansible_galaxy import repository_spec_parse
from ansible_galaxy.fetch import fetch_factory
from ansible_galaxy.models.repository_spec import FetchMethods
from ansible_galaxy.models.requirement import Requirement, RequirementOps
from ansible_galaxy.models.requirement_spec import RequirementSpec

log = logging.getLogger(__name__)


# TODO: revisit this since we don't have to emulate the 'ansible-galaxy install'
#       support for roles now, and could used different error handling
def raise_without_ignore(ignore_errors, msg=None, rc=1):
    """
    Exits with the specified return code unless the
    option --ignore-errors was specified
    """
    ignore_error_blurb = '- you can use --ignore-errors to skip failed collections and finish processing the list.'
    if not ignore_errors:
        # Note: msg may actually be an exception instance or a text string

        message = ignore_error_blurb
        if msg:
            message = '%s:\n%s' % (msg, ignore_error_blurb)
        # TODO: some sort of ignoreable exception
        raise exceptions.GalaxyError(message)


def _verify_requirements_repository_spec_have_namespaces(requirements_list):
    for requirement_to_install in requirements_list:
        req_spec = requirement_to_install.requirement_spec
        log.debug('repo install repository_spec: %s', req_spec)

        if not req_spec.namespace:
            raise exceptions.GalaxyRepositorySpecError(
                'The repository spec "%s" requires a namespace (either "namespace.name" or via --namespace)' % req_spec.spec_string,
                repository_spec=req_spec)


# pass a list of repository_spec objects
def install_repositories_matching_repository_specs(galaxy_context,
                                                   requirements_list,
                                                   editable=False,
                                                   namespace_override=None,
                                                   display_callback=None,
                                                   # TODO: error handling callback ?
                                                   ignore_errors=False,
                                                   no_deps=False,
                                                   force_overwrite=False):
    '''Install a set of repositories specified by repository_specs if they are not already installed'''

    # log.debug('editable: %s', editable)
    log.debug('requirements_list: %s', requirements_list)

    _verify_requirements_repository_spec_have_namespaces(requirements_list)

    # FIXME: mv mv this filtering to it's own method
    # match any of the content specs for stuff we want to install
    # ie, see if it is already installed
    requested_repository_specs = [x.requirement_spec for x in requirements_list]
    repository_spec_match_filter = matchers.MatchRepositorySpecNamespaceName(requested_repository_specs)

    irdb = installed_repository_db.InstalledRepositoryDatabase(galaxy_context)
    already_installed_generator = irdb.select(repository_spec_match_filter=repository_spec_match_filter)

    # FIXME: if/when GalaxyContent and InstalledGalaxyContent are attr.ib based and frozen and hashable
    #        we can simplify this filter with set ops

    already_installed_repository_spec_set = set([installed.repository_spec for installed in already_installed_generator])
    log.debug('already_installed_repository_spec_set: %s', already_installed_repository_spec_set)

    # This filters out already installed repositories unless --force. Aside from the warning, 'mazer install alikins.something_installed_already' is ok.
    requirements_to_install = [y for y in requirements_list if y.requirement_spec not in already_installed_repository_spec_set and not force_overwrite]

    log.debug('repository_specs_to_install: %s', pprint.pformat(requirements_to_install))

    return install_repositories(galaxy_context, requirements_to_install,
                                display_callback=display_callback,
                                ignore_errors=ignore_errors,
                                no_deps=no_deps,
                                force_overwrite=force_overwrite)


# FIXME: probably pass the point where passing around all the data to methods makes sense
#        so probably needs a stateful class here
def install_repository_specs_loop(galaxy_context,
                                  repository_spec_strings=None,
                                  requirements_list=None,
                                  editable=False,
                                  namespace_override=None,
                                  display_callback=None,
                                  # TODO: error handling callback ?
                                  ignore_errors=False,
                                  no_deps=False,
                                  force_overwrite=False):

    requirements_list = requirements_list or []

    for repository_spec_string in repository_spec_strings:
        fetch_method = \
            repository_spec_parse.choose_repository_fetch_method(repository_spec_string,
                                                                 editable=editable)
        log.debug('fetch_method: %s', fetch_method)

        if fetch_method == FetchMethods.LOCAL_FILE:
            # Since we only know this is a local file we vaguely recognize, we have to
            # open it up to get any more details. We _could_ attempt to parse the file
            # name, but that rarely ends well. Filename could also be arbitrary for downloads
            # from remote urls ('mazer install http://myci.example.com/somebuildjob/latest' etc)
            spec_data = collection_artifact.load_data_from_collection_artifact(repository_spec_string)
            spec_data['fetch_method'] = fetch_method
        elif fetch_method == FetchMethods.REMOTE_URL:
            # download the url
            # hope it is a collection artifact and use load_data_from_collection_artifact() for the
            # rest of the repo_spec data
            log.debug('repository_spec_string: %s', repository_spec_string)

            tmp_downloaded_path = download.fetch_url(repository_spec_string,
                                                     # Note: ignore_certs is meant for galaxy server,
                                                     # overloaded to apply for arbitrary http[s] downloads here
                                                     validate_certs=not galaxy_context.server['ignore_certs'])
            spec_data = collection_artifact.load_data_from_collection_artifact(tmp_downloaded_path)

            # pretend like this is a local_file install now
            spec_data['fetch_method'] = FetchMethods.LOCAL_FILE
        else:
            spec_data = repository_spec_parse.spec_data_from_string(repository_spec_string,
                                                                    namespace_override=namespace_override,
                                                                    editable=editable)

            spec_data['fetch_method'] = fetch_method

        log.debug('spec_data: %s', spec_data)

        req_spec = RequirementSpec.from_dict(spec_data)

        req = Requirement(repository_spec=None, op=RequirementOps.EQ, requirement_spec=req_spec)

        requirements_list.append(req)

    log.debug('requirements_list: %s', requirements_list)
    for req in requirements_list:
        display_callback('Installing %s' % req.requirement_spec.label, level='info')

    while True:
        if not requirements_list:
            break

        just_installed_repositories = \
            install_repositories_matching_repository_specs(galaxy_context,
                                                           requirements_list,
                                                           editable=editable,
                                                           namespace_override=namespace_override,
                                                           display_callback=display_callback,
                                                           ignore_errors=ignore_errors,
                                                           no_deps=no_deps,
                                                           force_overwrite=force_overwrite)

        # set the repository_specs to search for to whatever the install reported as being needed yet
        # requirements_list = new_requirements_list
        requirements_list = find_new_deps_from_installed(galaxy_context,
                                                         just_installed_repositories,
                                                         no_deps=no_deps)

        for req in requirements_list:
            if req.repository_spec:
                msg = 'Installing requirement %s (required by %s)' % (req.requirement_spec.label, req.repository_spec.label)
            else:
                msg = 'Installing requirement %s' % req.requirement_spec.label
            display_callback(msg, level='info')

    # FIXME: what results to return?
    return 0


def find_new_deps_from_installed(galaxy_context, installed_repos, no_deps=False):
    if no_deps:
        return []

    # FIXME: Just return the single item list installed_repositories here
    deps_and_reqs_set = set()

    log.debug('finding new deps for installed repos: %s',
              [str(x) for x in installed_repos])

    # Remove dupes. Note, can/will change ordering.
    # installed_repos = list(set(installed_repos))

    # install requirements ("dependcies" in collection info), if we want them
    for installed_repository in installed_repos:
        # log.debug('just_installed_repository: %s', installed_repository)

        # convert deps/reqs to sets. Losing any ordering, but avoids dupes
        reqs_set = set(installed_repository.requirements)

        deps_and_reqs_set.update(reqs_set)

        # for dep_req in sorted(deps_and_reqs_set):
        #    log.debug('deps_and_reqs_set_item: %s', dep_req)

    deps_and_reqs_list = sorted(list(deps_and_reqs_set))

    # log.debug('deps_and_reqs_list: %s', pf(deps_and_reqs_list))

    unsolved_deps_reqs = []
    for dep_req in deps_and_reqs_list:
        log.debug('Checking if %s is provided by something installed', str(dep_req))

        # Search for an exact ns_n_v match
        irdb = installed_repository_db.InstalledRepositoryDatabase(galaxy_context)
        already_installed_iter = irdb.by_requirement(dep_req)
        already_installed = list(already_installed_iter)

        log.debug('already_installed: %s', already_installed)

        solved = False
        for provider in already_installed:
            log.debug('The dep_req %s is already provided by %s', dep_req, provider)
            solved = solved or True

        if solved:
            log.debug('skipping dep_req %s', dep_req)
            continue

        unsolved_deps_reqs.append(dep_req)

    log.debug('Found additional requirements: %s', pprint.pformat(unsolved_deps_reqs))

    return unsolved_deps_reqs


# TODO: split into resolve, find/get metadata, resolve deps, download, install transaction
def install_repositories(galaxy_context,
                         requirements_to_install,
                         display_callback=None,
                         # TODO: error handling callback ?
                         ignore_errors=False,
                         no_deps=False,
                         force_overwrite=False):

    display_callback = display_callback or display.display_callback
    log.debug('requirements_to_install: %s', requirements_to_install)
    # log.debug('no_deps: %s', no_deps)
    # log.debug('force_overwrite: %s', force_overwrite)

    # dep_requirements = []
    most_installed_repositories = []

    # TODO: this should be adding the content/self.args/content_left to
    #       a list of needed deps

    # Remove any dupe repository_specs
    requirements_to_install_uniq = set(requirements_to_install)

    # TODO: if the default ordering of repository_specs isnt useful, may need to tweak it
    for requirement_to_install in sorted(requirements_to_install_uniq):
        log.debug('requirement_to_install: %s', requirement_to_install)
        installed_repositories = install_repository(galaxy_context,
                                                    requirement_to_install,
                                                    display_callback=display_callback,
                                                    ignore_errors=ignore_errors,
                                                    no_deps=no_deps,
                                                    force_overwrite=force_overwrite)

        # log.debug('dep_requirement_repository_specs1: %s', dep_requirements)

        if not installed_repositories:
            log.debug('install_repository() returned None for requirement_to_install: %s', requirement_to_install)
            continue

        for installed_repo in installed_repositories:
            required_by_blurb = ''
            if requirement_to_install.repository_spec:
                required_by_blurb = ' (required by %s)' % requirement_to_install.repository_spec.label

            log.info('Installed: %s %s to %s%s',
                     installed_repo.label,
                     installed_repo.repository_spec.version,
                     installed_repo.path,
                     required_by_blurb)

        most_installed_repositories.extend(installed_repositories)
        # dep_requirements.extend(new_dep_requirements)

    return most_installed_repositories


def install_repository(galaxy_context,
                       requirement_to_install,
                       display_callback=None,
                       # TODO: error handling callback ?
                       ignore_errors=False,
                       no_deps=False,
                       force_overwrite=False):
    '''This installs a single package by finding it, fetching it, verifying it and installing it.'''

    display_callback = display_callback or display.display_callback

    # INITIAL state
    # dep_requirements = []

    # TODO: we could do all the downloads first, then install them. Likely
    #       less error prone mid 'transaction'
    log.debug('Processing %r', requirement_to_install)

    repository_spec_to_install = requirement_to_install.requirement_spec
    requirement_spec_to_install = requirement_to_install.requirement_spec

    # else trans to ... FIND_FETCHER?

    # TODO: check if already installed and move to approriate state

    log.debug('About to find() requested requirement_spec_to_install: %s', requirement_spec_to_install)

    # potential_repository_spec is a repo spec for the install candidate we potentially found.
    irdb = installed_repository_db.InstalledRepositoryDatabase(galaxy_context)
    log.debug('Checking to see if %s is already installed', requirement_spec_to_install)

    already_installed_iter = irdb.by_requirement_spec(requirement_spec_to_install)
    already_installed = sorted(list(already_installed_iter))

    log.debug('already_installed: %s', already_installed)

    if already_installed:
        for already_installed_repository in already_installed:
            display_callback('%s is already installed at %s' % (already_installed_repository.repository_spec.label,
                                                                already_installed_repository.path),
                             level='warning')
        log.debug('Stuff %s was already installed. In %s', requirement_spec_to_install, already_installed)

        return None

    # We dont have anything that matches the RequirementSpec installed
    fetcher = fetch_factory.get(galaxy_context=galaxy_context,
                                requirement_spec=requirement_spec_to_install)

    # if we fail to get a fetcher here, then to... FIND_FETCHER_FAILURE ?
    # could also move some of the logic in fetcher_factory to be driven from here
    # and make the steps of mapping repository spec -> fetcher method part of the
    # state machine. That might be a good place to support multiple galaxy servers
    # or preferring local content to remote content, etc.

    # FIND state
    # See if we can find metadata and/or download the archive before we try to
    # remove an installed version...
    try:
        find_results = install.find(fetcher)
    except exceptions.GalaxyError as e:
        log.debug('requirement_to_install %s failed to be met: %s', requirement_to_install, e)
        log.warning('Unable to find metadata for %s: %s', requirement_spec_to_install.label, e)
        # FIXME: raise dep error exception?
        raise_without_ignore(ignore_errors, e)
        # continue
        return None

    # TODO: make sure repository_spec version is correct and set

    # TODO: state transition, if find_results -> INSTALL
    #       if not, then FIND_FAILED

    # TODO/FIXME: We give find() a RequirementSpec, but find_results should have enough
    #             info to create a concrete RepositorySpec

    # TODO: if we want client side content whitelist/blacklist, or pinned versions,
    #       or rules to only update within some semver range (ie, only 'patch' level),
    #       we could hook rule validation stuff here.

    # TODO: build a new repository_spec based on what we actually fetched to feed to
    #       install etc. The fetcher.fetch() could return a datastructure needed to build
    #       the new one instead of doing it in verify()
    found_repository_spec = install.repository_spec_from_find_results(find_results,
                                                                      requirement_spec_to_install)

    log.debug('found_repository_spec: %s', found_repository_spec)

    repository_spec_to_install = found_repository_spec
    log.debug('About to download repository requested by %s: %s', requirement_spec_to_install, repository_spec_to_install)

    # FETCH state
    try:
        fetch_results = install.fetch(fetcher,
                                      repository_spec=repository_spec_to_install,
                                      find_results=find_results)
        log.debug('fetch_results: %s', fetch_results)
        # fetch_results will include a 'archive_path' pointing to where the artifact
        # was saved to locally.
    except exceptions.GalaxyError as e:
        # fetch error probably should just go to a FAILED state, at least until
        # we have to implement retries
        log.warning('Unable to fetch %s: %s', repository_spec_to_install.name, e)
        raise_without_ignore(ignore_errors, e)
        # continue
        # FIXME: raise ?
        return None

    # FIXME: seems like we want to resolve deps before trying install
    #        We need the role (or other content) deps from meta before installing
    #        though, and sometimes (for galaxy case) we dont know that until we've downloaded
    #        the file, which we dont do until somewhere in the begin of content.install (fetch).
    #        We can get that from the galaxy API though.
    #
    # FIXME: exc handling

    installed_repositories = []

    try:
        installed_repositories = install.install(galaxy_context,
                                                 fetcher,
                                                 fetch_results,
                                                 repository_spec=found_repository_spec,
                                                 force_overwrite=force_overwrite,
                                                 display_callback=display_callback)
    except exceptions.GalaxyError as e:
        msg = "- %s was NOT installed successfully: %s "
        display_callback(msg % (found_repository_spec.label, e), level='warning')
        log.warning(msg, found_repository_spec.label, str(e))
        raise_without_ignore(ignore_errors, e)
        return []

    if not installed_repositories:
        log.warning("- %s was NOT installed successfully.", found_repository_spec.label)
        raise_without_ignore(ignore_errors)

    return installed_repositories
