
import logging
import os

from ansible_galaxy.build import Build, BuildStatuses
from ansible_galaxy import collection_info

log = logging.getLogger(__name__)


def _build(galaxy_context,
           build_context,
           display_callback=None):

    results = {}

    log.debug('build_context: %s', build_context)

    collection_src_root = build_context.collection_src_root
    collection_info_file_path = os.path.join(collection_src_root, collection_info.DEFAULT_FILENAME)

    results['src_root'] = collection_src_root
    results['info_file_path'] = collection_info_file_path
    results['errors'] = []

    info = None

    with open(collection_info_file_path, 'r') as info_fd:
        info = collection_info.load(info_fd)

        log.debug('info: %s', info)
        display_callback('%s' % info)

    if not info:
        results['success'] = False
        results['errors'].append('There was no collection info in %s' % collection_info_file_path)
        return results

    builder = Build(build_context=build_context,
                    collection_info=info)

    build_results = builder.run(display_callback=display_callback)

    log.debug('build_results: %s', build_results)

    # results here include the builder results and... ?
    results['build_results'] = build_results

    log.debug('build action results: %s', results)

    if build_results.status == BuildStatuses.success:
        results['success'] = True
        return results

    results['success'] = False
    return results


def build(galaxy_context,
          build_context,
          display_callback=None):
    '''Run _list action and return an exit code suitable for process exit'''

    results = _build(galaxy_context,
                     build_context,
                     display_callback=display_callback)

    log.debug('cli build action results: %s', results)

    if results['success']:
        return os.EX_OK  # 0

    return os.EX_SOFTWARE  # 70
