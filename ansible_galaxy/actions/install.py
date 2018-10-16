import logging
import os
import pprint

from ansible_galaxy import display
from ansible_galaxy import exceptions
from ansible_galaxy import content_spec
from ansible_galaxy import install
from ansible_galaxy import installed_collection_db
from ansible_galaxy import matchers
from ansible_galaxy import requirements
from ansible_galaxy.utils import yaml_parse

log = logging.getLogger(__name__)


def raise_without_ignore(ignore_errors, msg=None, rc=1):
    """
    Exits with the specified return code unless the
    option --ignore-errors was specified
    """
    ignore_error_blurb = '- you can use --ignore-errors to skip failed roles and finish processing the list.'
    if not ignore_errors:
        message = ignore_error_blurb
        if msg:
            message = '%s:\n%s' % (msg, ignore_error_blurb)
        # TODO: some sort of ignoreable exception
        raise exceptions.GalaxyError(message)


def _verify_content_specs_have_namespace(collection_specs):
    content_spec_list = []

    for collection_spec in collection_specs:
        # FIXME: be consistent about collection/content
        content_spec_ = collection_spec

        log.info('content install content_spec: %s', content_spec_)

        if not content_spec_.namespace:
            raise exceptions.GalaxyContentSpecError(
                'The content spec "%s" requires a namespace (either "namespace.name" or via --namespace)' % content_spec_.spec_string,
                content_spec=content_spec_)

        content_spec_list.append(content_spec_)

    return content_spec_list


# pass a list of content_spec objects
def install_collections_matching_collection_specs(galaxy_context,
                                                  collection_specs,
                                                  editable=False,
                                                  namespace_override=None,
                                                  display_callback=None,
                                                  # TODO: error handling callback ?
                                                  ignore_errors=False,
                                                  no_deps=False,
                                                  force_overwrite=False):
    '''Install a set of packages specified by collection_spec_strings if they are not already installed'''

    log.debug('editable: %s', editable)
    log.debug('collection_specs: %s', collection_specs)

    requested_content_specs = _verify_content_specs_have_namespace(collection_specs=collection_specs)

    # FIXME: mv mv this filtering to it's own method
    # match any of the content specs for stuff we want to install
    # ie, see if it is already installed
    collection_match_filter = matchers.MatchContentSpec([x for x in requested_content_specs])

    icdb = installed_collection_db.InstalledCollectionDatabase(galaxy_context)
    already_installed_generator = icdb.select(collection_match_filter=collection_match_filter)

    log.debug('requested_content_specs before: %s', requested_content_specs)

    # FIXME: if/when GalaxyContent and InstalledGalaxyContent are attr.ib based and frozen and hashable
    #        we can simplify this filter with set ops

    already_installed_content_spec_set = set([installed.content_spec for installed in already_installed_generator])
    log.debug('already_installed_content_spec_set: %s', already_installed_content_spec_set)

    if already_installed_content_spec_set and not force_overwrite:
        msg = 'The following packages are already installed. Use --force to overwrite:\n%s' % \
            '\n'.join([x.label for x in already_installed_content_spec_set])

        raise exceptions.GalaxyError(msg)

    content_specs_to_install = [y for y in requested_content_specs if y not in already_installed_content_spec_set or force_overwrite]
    log.debug('content_specs_to_install: %s', pprint.pformat(content_specs_to_install))

    log.debug('content_specs_to_install after: %s', content_specs_to_install)

    return install_collections(galaxy_context, content_specs_to_install,
                               display_callback=display_callback,
                               ignore_errors=ignore_errors,
                               no_deps=no_deps,
                               force_overwrite=force_overwrite)


# FIXME: probably pass the point where passing around all the data to methods makes sense
#        so probably needs a stateful class here
def install_collection_specs_loop(galaxy_context,
                                  collection_spec_strings=None,
                                  requirement_specs=None,
                                  editable=False,
                                  namespace_override=None,
                                  display_callback=None,
                                  # TODO: error handling callback ?
                                  ignore_errors=False,
                                  no_deps=False,
                                  force_overwrite=False):

    requirement_specs = requirement_specs or []

    # Turn the collection / requirement names from the cli into a list of RequirementSpec objects
    if collection_spec_strings:
        more_req_specs = requirements.from_requirement_spec_strings(collection_spec_strings,
                                                                    editable=editable)
        log.debug('more_req_specs: %s', more_req_specs)

        # a new list is ok/better here
        requirement_specs += more_req_specs

    log.debug('req_specs: %s', requirement_specs)

    while True:
        if not requirement_specs:
            break

        new_requested_collection_specs = \
            install_collections_matching_collection_specs(galaxy_context,
                                                          requirement_specs,
                                                          editable=editable,
                                                          namespace_override=namespace_override,
                                                          display_callback=display_callback,
                                                          ignore_errors=ignore_errors,
                                                          no_deps=no_deps,
                                                          force_overwrite=force_overwrite)

        log.debug('new_requested_collection_specs: %s', pprint.pformat(new_requested_collection_specs))

        # set the content_specs to search for to whatever the install reported as being needed yet
        requirement_specs = new_requested_collection_specs

    # FIXME: what results to return?
    return 0


# TODO: split into resolve, find/get metadata, resolve deps, download, install transaction
def install_collections(galaxy_context,
                        content_specs_to_install,
                        display_callback=None,
                        # TODO: error handling callback ?
                        ignore_errors=False,
                        no_deps=False,
                        force_overwrite=False):

    display_callback = display_callback or display.display_callback
    log.debug('content_specs_to_install: %s', content_specs_to_install)
    log.debug('no_deps: %s', no_deps)
    log.debug('force_overwrite: %s', force_overwrite)

    dep_requirement_content_specs = []

    # FIXME - Need to handle role files here for backwards compat

    # TODO: this should be adding the content/self.args/content_left to
    #       a list of needed deps

    # FIXME: should be while? or some more func style processing
    #        iterating until there is nothing left
    for content_spec_to_install in content_specs_to_install:
        log.debug('content_spec_to_install: %s', content_spec_to_install)
        new_dep_requirement_content_specs = install_collection(galaxy_context,
                                                               content_spec_to_install,
                                                               display_callback=display_callback,
                                                               ignore_errors=ignore_errors,
                                                               no_deps=no_deps,
                                                               force_overwrite=force_overwrite)

        log.debug('new_dep_requirement_content_specs: %s', pprint.pformat(new_dep_requirement_content_specs))
        log.debug('dep_requirement_content_specs1: %s', pprint.pformat(dep_requirement_content_specs))

        if not new_dep_requirement_content_specs:
            log.debug('install_collection return None for content_spec_to_install: %s', content_spec_to_install)
            continue

        dep_requirement_content_specs.extend(new_dep_requirement_content_specs)

        log.debug('dep_requirement_content_specs2: %s', pprint.pformat(dep_requirement_content_specs))
        # dep_requirement_content_specs.extend(new_dep_requirement_content_specs)
        # only process roles in roles files when names matches if given

    return dep_requirement_content_specs


def install_collection(galaxy_context,
                       content_spec_to_install,
                       display_callback=None,
                       # TODO: error handling callback ?
                       ignore_errors=False,
                       no_deps=False,
                       force_overwrite=False):
    '''This installs a single package by finding it, fetching it, verifying it and installing it.'''

    # INITIAL state
    dep_requirement_content_specs = []

    # TODO: we could do all the downloads first, then install them. Likely
    #       less error prone mid 'transaction'
    log.debug('Processing %s', content_spec_to_install.name)

    if content_spec_to_install.fetch_method == content_spec.FetchMethods.EDITABLE:
        # trans to INSTALL_EDITABLE state
        install_editable_content(content_spec_to_install)
        # check results, then transition to either DONE or INSTALL_EDIBLE_FAILED
        log.debug('not installing/extractings because of install_collection')
        return
    # else trans to ... FIND_FETCHER?

    log.debug('About to find() requested content_spec_to_install: %s', content_spec_to_install)

    fetcher = install.fetcher(galaxy_context, content_spec=content_spec_to_install)
    # if we fail to get a fetcher here, then to... FIND_FETCHER_FAILURE ?
    # could also move some of the logic in fetcher_factory to be driven from here
    # and make the steps of mapping collection spec -> fetcher method part of the
    # state machine. That might be a good place to support multiple galaxy servers
    # or preferring local content to remote content, etc.

    # FIND state
    # See if we can find metadata and/or download the archive before we try to
    # remove an installed version...
    try:
        find_results = install.find(fetcher, content_spec=content_spec_to_install)
        # log.debug('standalone find_results: %s', pprint.pformat(find_results))
    except exceptions.GalaxyError as e:
        log.warning('Unable to find metadata for %s: %s', content_spec_to_install.name, e)
        # FIXME: raise dep error exception?
        raise_without_ignore(ignore_errors, e)
        # continue
        return None

    # TODO: make sure content_spec version is correct and set

    # TODO: state transition, if find_results -> INSTALL
    #       if not, then FIND_FAILED

    log.debug('About to download requested content_spec_to_install: %s', content_spec_to_install)

    # FETCH state
    try:
        fetch_results = install.fetch(fetcher,
                                      content_spec=content_spec_to_install,
                                      find_results=find_results)
        log.debug('fetch_results: %s', fetch_results)
        # fetch_results will include a 'archive_path' pointing to where the artifact
        # was saved to locally.
    except exceptions.GalaxyError as e:
        # fetch error probably should just go to a FAILED state, at least until
        # we have to implement retries
        log.warning('Unable to fetch %s: %s', content_spec_to_install.name, e)
        raise_without_ignore(ignore_errors, e)
        # continue
        # FIXME: raise ?
        return None

    # TODO: if we want client side content whitelist/blacklist, or pinned versions,
    #       or rules to only update within some semver range (ie, only 'patch' level),
    #       we could hook rule validation stuff here.

    # TODO: build a new content_spec based on what we actually fetched to feed to
    #       install etc. The fetcher.fetch() could return a datastructure needed to build
    #       the new one instead of doing it in verify()
    fetched_content_spec = install.update_content_spec(fetch_results,
                                                       content_spec_to_install)

    log.debug('fetched_content_spec: %s', fetched_content_spec)

    # FIXME: seems like we want to resolve deps before trying install
    #        We need the role (or other content) deps from meta before installing
    #        though, and sometimes (for galaxy case) we dont know that until we've downloaded
    #        the file, which we dont do until somewhere in the begin of content.install (fetch).
    #        We can get that from the galaxy API though.
    #
    # FIXME: exc handling
    try:
        installed = install.install(galaxy_context,
                                    fetcher,
                                    fetch_results,
                                    # content.content_meta,
                                    content_spec=fetched_content_spec,
                                    force_overwrite=force_overwrite)
    except exceptions.GalaxyError as e:
        log.exception(e)
        log.warning("- %s was NOT installed successfully: %s ", fetched_content_spec.name, str(e))
        raise


        # raise_without_ignore(ignore_errors, e)


        return None
        # continue

    log.debug('installed result: %s', installed)

    if not installed:
        log.warning("- %s was NOT installed successfully.", fetched_content_spec.label)
        raise_without_ignore(ignore_errors)

    log.debug('installed: %s', pprint.pformat(installed))
    if no_deps:
        log.warning('- %s was installed but any deps will not be installed because of no_deps',
                    fetched_content_spec.label)

    # TODO?: update the install receipt for 'installed' if succesull?
    # oh dear god, a dep solver...

    if no_deps:
        return dep_requirement_content_specs

    # FIXME: should install all of init 'deps', then build a list of new deps, and repeat

    # install dependencies, if we want them
    # FIXME - Galaxy Content Types handle dependencies in the GalaxyContent type itself because
    #         a content repo can contain many types and many of any single type and it's just
    #         easier to have that introspection there. In the future this should be more
    #         unified and have a clean API
    for installed_content in installed:
        log.debug('installed_content: %s', installed_content)

        # TODO: generalize to collections/repos
        # if installed_content.content_type == "role":
        if not installed_content.meta_main:
            log.warning("Meta file %s is empty. Skipping meta main dependencies.", installed_content.path)
            # continue

        # TODO: InstalledContent -> InstalledCollection
        #       GalaxyContent -> GalaxyCollection (and general getting rid of GalaxyContent)
        #       InstalledCollection.requirements for install time requirements
        #        so collections and trad roles have same interface
        collection_dependencies = installed_content.requirements or []
        # if installed_content.meta_main:
        #    collection_dependencies = installed_content.meta_main.dependencies or []
        log.debug('collection_dependencies: %s', pprint.pformat(collection_dependencies))

        # TODO: also check for Collections requirements.yml via Collection.requirements?
        #       and/or requirements in its MANIFEST.json

        for dep in collection_dependencies:
            log.debug('Installing dep %s', dep)

            # dep_info = yaml_parse.yaml_parse(dep)
            # log.debug('dep_info: %s', pprint.pformat(dep_info))

            # if '.' not in dep_info['name'] and '.' not in dep_info['src'] and dep_info['scm'] is None:
            #    log.debug('the dep %s doesnt look like a galaxy dep, skipping for now', dep_info)
            #    # we know we can skip this, as it's not going to
            #    # be found on galaxy.ansible.com
            #    continue

            dep_requirement_content_specs.append(dep)

    log.debug('dep_requirement_content_specs: %s', pprint.pformat(dep_requirement_content_specs))
    return dep_requirement_content_specs
    # return 0

# def role_install_post_check():
#    if False:
#        dep_role = GalaxyContent(galaxy_context, **dep_info)
#
#        if '.' not in dep_role.name and '.' not in dep_role.src and dep_role.scm is None:
#            # we know we can skip this, as it's not going to
#            # be found on galaxy.ansible.com
#            continue
#        if dep_role.install_info is None:
#            if dep_role not in requested_contents:
#                display_callback('- adding dependency: %s' % str(dep_role))
#                requested_contents.append(dep_role)
#            else:
#                display_callback('- dependency %s already pending installation.' % dep_role.name)
#        else:
#            if dep_role.install_info['version'] != dep_role.version:
#                log.warning('- dependency %s from role %s differs from already installed version (%s), skipping',
#                            str(dep_role), installed_content.name, dep_role.install_info['version'])
#            else:
#                display_callback('- dependency %s is already installed, skipping.' % dep_role.name)

    # TODO: Need some sort of ContentTransaction for encapsulating pairs of remove and install


# FIXME: do we need this? archive.extract_files() may do this for us now
def stuff_for_updating(content, display_callback, force_overwrite=False):

    #       (or any set of ops needed)
    # FIXME - Unsure if we want to handle the install info for all galaxy
    #         content. Skipping for non-role types for now.
    # FIXME: this is just deciding if the content is installed or not, should check for it in
    #        a 'installed_content_db' once we have one
    if content.content_type == "role":
        if content.install_info is not None:
            # FIXME: seems like this should be up to the content type specific serializer/installer to figure out
            # FIXME: this just checks for version difference, will need to enfore update/replace policy somewhre
            if content.install_info['version'] != content.version or force_overwrite:
                if force_overwrite:
                    display_callback('- changing role %s from %s to %s' %
                                     (content.name, content.install_info['version'], content.version or "unspecified"))
                    # FIXME: when we get to setting up a tranaction/update plan,
                    #        this would add a remove step there and an install
                    #        step (or an update maybe)
                    content.remove()
                else:
                    # eventually need to build a results object here
                    log.warn('- %s (%s) is already installed - use --force to change version to %s',
                             content.name, content.install_info['version'], content.version or "unspecified")
                    # continue
                    return None
            else:
                if not force_overwrite:
                    display_callback('- %s is already installed, skipping.' % str(content))
                    # continue
                    return None


def install_editable_content(content):
    '''Link the content path to the local checkout, similar to pip install -e'''

    # is it a directory or is it a tarball?
    if not os.path.isdir(os.path.abspath(content.src)):
        log.warning("%s needs to be a local directory for an editable install" % content.src)
        raise_without_ignore(None, None)

    namespace = content.content_spec.namespace
    repository = content.content_spec.name
    dst_ns_root = os.path.join(content.path, namespace)
    dst_repo_root = os.path.join(content.path, namespace, repository)

    if not os.path.exists(dst_ns_root):
        os.makedirs(dst_ns_root)

    if not os.path.exists(dst_repo_root):
        os.symlink(os.path.abspath(content.src), dst_repo_root)
