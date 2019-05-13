
import logging
import os

from ansible_galaxy.build import Build, BuildStatuses
from ansible_galaxy import collection_info

log = logging.getLogger(__name__)


def ensure_output_dir(output_path):
    if not os.path.isdir(output_path):
        log.debug('Creating output_path: %s', output_path)
        os.makedirs(output_path)
    return output_path


def _build(galaxy_context,
           build_context,
           display_callback=None):

    results = {}

    log.debug('build_context: %s', build_context)

    collection_path = build_context.collection_path
    collection_info_file_path = os.path.join(collection_path, collection_info.COLLECTION_INFO_FILENAME)

    results['collection_path'] = collection_path
    results['info_file_path'] = collection_info_file_path
    results['errors'] = []
    results['success'] = False

    info = None

    try:
        with open(collection_info_file_path, 'r') as info_fd:
            info = collection_info.load(info_fd)

            log.debug('info: %s', info)
    except (IOError, ValueError) as e:
        log.error('Error loading the %s at %s: %s', collection_info.COLLECTION_INFO_FILENAME, collection_info_file_path, e)
        results['errors'].append('Error loading the %s at %s' % (collection_info.COLLECTION_INFO_FILENAME,
                                                                 collection_info_file_path))
        results['errors'].append(str(e))
        return results

    if not info:
        results['errors'].append('There was no collection info in %s' % collection_info_file_path)
        return results

    builder = Build(build_context=build_context,
                    collection_info=info)

    ensure_output_dir(build_context.output_path)

    build_results = builder.run(display_callback=display_callback)

    log.debug('build_results: %s', build_results)

    # results here include the builder results and... ?
    results['build_results'] = build_results

    log.debug('build action results: %s', results)

    if build_results.status == BuildStatuses.success:
        results['success'] = True
        return results

    return results


def build(galaxy_context,
          build_context,
          display_callback=None):
    '''Run _list action and return an exit code suitable for process exit'''

    results = _build(galaxy_context,
                     build_context,
                     display_callback=display_callback)

    log.debug('cli build action results: %s', results)

    if results['errors']:
        for error in results['errors']:
            display_callback(error)

    if results['success']:
        return os.EX_OK  # 0

    return os.EX_SOFTWARE  # 70
