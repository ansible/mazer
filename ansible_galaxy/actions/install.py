import logging
import os

from ansible_galaxy import display
from ansible_galaxy import exceptions
from ansible_galaxy import content_spec
from ansible_galaxy.utils import yaml_parse

# FIXME: get rid of flat_rest_api
from ansible_galaxy.flat_rest_api.content import GalaxyContent

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


# FIXME: install_content_type is wrong, should be option to GalaxyContent.install()?
# TODO: this will eventually be replaced by a content_spec 'resolver' that may
#       hit galaxy api
def _build_content_set(content_spec_strings, install_content_type, galaxy_context,
                       namespace_override=None, editable=False):
    # TODO: split this into methods that build GalaxyContent items from the content_specs
    #       and another that installs a set of GalaxyContents
    # roles were specified directly, so we'll just go out grab them
    # (and their dependencies, unless the user doesn't want us to).

    # FIXME: could be a generator...
    content_left = []

    for content_spec_string in content_spec_strings:
        content_spec_ = content_spec.content_spec_from_string(content_spec_string.strip(),
                                                              namespace_override=namespace_override,
                                                              editable=editable)

        log.info('content install content_spec: %s', content_spec_)

        if not content_spec_.namespace:
            raise exceptions.GalaxyContentSpecError(
                'The content spec "%s" requires a namespace (either "namespace.name" or via --namespace)' % content_spec_.spec_string,
                content_spec=content_spec_)

        # TODO: a content spec resolver to extend this info, find it, build a GalaxyContent
        #       and return it.
        content_left.append(GalaxyContent(galaxy_context,
                                          namespace=content_spec_.namespace,
                                          name=content_spec_.name,
                                          src=content_spec_.src,
                                          scm=content_spec_.scm,
                                          version=content_spec_.version,
                                          content_spec=content_spec_,
                                          ))

    return content_left


# pass a list of content_spec objects
def install_content_specs(galaxy_context, content_spec_strings, install_content_type,
                          editable=False,
                          namespace_override=None,
                          display_callback=None,
                          # TODO: error handling callback ?
                          ignore_errors=False,
                          no_deps=False,
                          force_overwrite=False):
    log.debug('editable: %s', editable)
    log.debug('content_spec_strings: %s', content_spec_strings)
    log.debug('install_content_type: %s', install_content_type)

    requested_contents = _build_content_set(content_spec_strings=content_spec_strings,
                                            install_content_type=install_content_type,
                                            galaxy_context=galaxy_context,
                                            namespace_override=namespace_override,
                                            editable=editable)

    return install_contents(galaxy_context, requested_contents, install_content_type,
                            display_callback=display_callback,
                            ignore_errors=ignore_errors,
                            no_deps=no_deps,
                            force_overwrite=force_overwrite)


def install_contents(galaxy_context, requested_contents, install_content_type,
                     display_callback=None,
                     # TODO: error handling callback ?
                     ignore_errors=False,
                     no_deps=False,
                     force_overwrite=False):

    display_callback = display_callback or display.display_callback
    log.debug('requested_contents: %s', requested_contents)
    log.debug('install_content_type: %s', install_content_type)
    log.debug('no_deps: %s', no_deps)
    log.debug('force_overwrite: %s', force_overwrite)

    # FIXME - Need to handle role files here for backwards compat

    # TODO: this should be adding the content/self.args/content_left to
    #       a list of needed deps

    # FIXME: should be while? or some more func style processing
    #        iterating until there is nothing left
    for content in requested_contents:
        # only process roles in roles files when names matches if given

        # FIXME - not sure how to handle this scenario for ansible galaxy files
        #         here or if we even want to handle that scenario because of
        #         the galaxy content allowing blank repos to be inspected
        #
        #         maybe we want this but only for role types for backwards
        #         compat
        #
        # if role_file and self.args and role.name not in self.args:
        #    display.vvv('Skipping role %s' % role.name)
        #    continue

        # TODO: we could do all the downloads first, then install them. Likely
        #       less error prone mid 'transaction'
        log.debug('Processing %s as %s', content.name, content.content_type)

        if content.content_spec.fetch_method == content_spec.FetchMethods.EDITABLE:
            install_editable_content(content)
            continue

        log.debug('About to find() requested content: %s', content)

        # See if we can find metadata and/or download the archive before we try to
        # remove an installed version...
        try:
            content.find()
        except exceptions.GalaxyError as e:
            log.warning('Unable to find metadata for %s: %s', content.name, e)
            raise_without_ignore(ignore_errors, e)
            continue

        log.debug('About to download requested content: %s', content)

        try:
            content.fetch()
        except exceptions.GalaxyError as e:
            log.warning('Unable to fetch %s: %s', content.name, e)
            raise_without_ignore(ignore_errors, e)
            continue

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
                        continue
                else:
                    if not force_overwrite:
                        display_callback('- %s is already installed, skipping.' % str(content))
                        continue

        # FIXME: seems like we want to resolve deps before trying install
        #        We need the role (or other content) deps from meta before installing
        #        though, and sometimes (for galaxy case) we dont know that until we've downloaded
        #        the file, which we dont do until somewhere in the begin of content.install (fetch).
        #        We can get that from the galaxy API though.
        #
        try:
            installed = content.install(force_overwrite=force_overwrite)
        except exceptions.GalaxyError as e:
            log.warning("- %s was NOT installed successfully: %s ", content.name, str(e))
            raise_without_ignore(ignore_errors, e)
            continue

        if not installed:
            log.warning("- %s was NOT installed successfully.", content.name)
            raise_without_ignore(ignore_errors)

        if no_deps:
            log.warning('- %s was installed but any deps will not be installed because of no_deps',
                        content.name)

        # oh dear god, a dep solver...

        # FIXME: should install all of init 'deps', then build a list of new deps, and repeat

        # install dependencies, if we want them
        # FIXME - Galaxy Content Types handle dependencies in the GalaxyContent type itself because
        #         a content repo can contain many types and many of any single type and it's just
        #         easier to have that introspection there. In the future this should be more
        #         unified and have a clean API
        if content.content_type == "role":
            if not no_deps and installed:
                if not content.metadata:
                    log.warning("Meta file %s is empty. Skipping dependencies.", content.path)
                else:
                    role_dependencies = content.metadata.get('dependencies') or []
                    for dep in role_dependencies:
                        log.debug('Installing dep %s', dep)
                        dep_info = yaml_parse.yaml_parse(dep)
                        dep_role = GalaxyContent(galaxy_context, **dep_info)
                        if '.' not in dep_role.name and '.' not in dep_role.src and dep_role.scm is None:
                            # we know we can skip this, as it's not going to
                            # be found on galaxy.ansible.com
                            continue
                        if dep_role.install_info is None:
                            if dep_role not in requested_contents:
                                display_callback('- adding dependency: %s' % str(dep_role))
                                requested_contents.append(dep_role)
                            else:
                                display_callback('- dependency %s already pending installation.' % dep_role.name)
                        else:
                            if dep_role.install_info['version'] != dep_role.version:
                                log.warning('- dependency %s from role %s differs from already installed version (%s), skipping',
                                            str(dep_role), content.name, dep_role.install_info['version'])
                            else:
                                display_callback('- dependency %s is already installed, skipping.' % dep_role.name)

    return 0


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
