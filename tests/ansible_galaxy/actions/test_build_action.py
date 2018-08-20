import logging
import os

from ansible_galaxy.actions import build
from ansible_galaxy.models.build_context import BuildContext

log = logging.getLogger(__name__)


# FIXME: generalize/share
def display_callback(msg, **kwargs):
    log.debug(msg)


def test_build(galaxy_context, tmpdir):
    output_path = tmpdir.mkdir('mazer_test_build_action_test_build')

    collection_path = os.path.join(os.path.dirname(__file__), '../', 'collection_examples/hello')
    build_context = BuildContext(collection_path, output_path=output_path.strpath)
    ret = build.build(galaxy_context, build_context, display_callback)
    log.debug('ret: %s', ret)

    assert ret == 0, 'build action return code was not 0 but was %s' % ret
