import logging
import mock

from ansible_galaxy.actions import install
from ansible_galaxy import exceptions
from ansible_galaxy import content_spec
from ansible_galaxy import requirements

log = logging.getLogger(__name__)


def display_callback(msg, **kwargs):
    log.debug(msg)


def test_install_contents_empty_contents(galaxy_context):
    content_specs_to_install = []

    ret = install.install_collections(galaxy_context,
                                      content_specs_to_install=content_specs_to_install,
                                      display_callback=display_callback)

    log.debug('ret: %s', ret)
    assert isinstance(ret, list)
    assert ret == []


def test_install_collections(galaxy_context, mocker):
    needed_deps = requirements.from_requirement_spec_strings(['some_namespace.some_name'])

    content_specs_to_install = \
        [content_spec.content_spec_from_string('some_namespace.this_requires_some_name')]

    mocker.patch('ansible_galaxy.actions.install.install_collection',
                 return_value=needed_deps)

    ret = install.install_collections(galaxy_context,
                                      content_specs_to_install=content_specs_to_install,
                                      display_callback=display_callback)

    log.debug('ret: %s', ret)
    assert isinstance(ret, list)
    assert ret == needed_deps


def test_install_collections_no_deps_required(galaxy_context, mocker):
    needed_deps = []

    content_specs_to_install = \
        [content_spec.content_spec_from_string('some_namespace.this_requires_nothing')]

    # mock out install_collection
    mocker.patch('ansible_galaxy.actions.install.install_collection',
                 return_value=[])

    ret = install.install_collections(galaxy_context,
                                      content_specs_to_install=content_specs_to_install,
                                      display_callback=display_callback)

    log.debug('ret: %s', ret)
    assert isinstance(ret, list)
    assert ret == needed_deps


def test_verify_content_specs_have_namespace_empty(galaxy_context):
    ret = install._verify_content_specs_have_namespace([])

    log.debug('ret: %s', ret)
    assert isinstance(ret, list)
    assert ret == []


# even though 'blrp' isnt a valid spec, _build_content_set return something for now
def test_verify_content_specs_have_namespace(galaxy_context):
    content_spec = mock.Mock(namespace=None)
    try:
        install._verify_content_specs_have_namespace([content_spec])
    except exceptions.GalaxyError as e:
        log.exception(e)
        return

    assert False, 'Expected a GalaxyError to be raised here since the content_spec %s has no namespace or dots' % content_spec
