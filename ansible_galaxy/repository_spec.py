import logging
import os

from ansible_galaxy import galaxy_repository_spec
from ansible_galaxy import repository_spec_parse
from ansible_galaxy import exceptions

from ansible_galaxy.models.repository_spec import RepositorySpec, FetchMethods


log = logging.getLogger(__name__)


def is_scm(repository_spec_string):
    if '://' in repository_spec_string or '@' in repository_spec_string:
        return True

    return False


def choose_repository_fetch_method(repository_spec_string, editable=False):
    log.debug('repository_spec_string: %s', repository_spec_string)

    if is_scm(repository_spec_string):
        # create tar file from scm url
        return FetchMethods.SCM_URL

    comma_parts = repository_spec_string.split(',', 1)
    potential_filename = comma_parts[0]
    fetch_method = None
    if editable and os.path.isdir(potential_filename):
        fetch_method = FetchMethods.EDITABLE
    elif os.path.isfile(potential_filename):
        # installing a local tar.gz
        fetch_method = FetchMethods.LOCAL_FILE
    elif '://' in repository_spec_string:
        fetch_method = FetchMethods.REMOTE_URL
    elif '.' in repository_spec_string and len(repository_spec_string.split('.', 1)) == 2:
        fetch_method = FetchMethods.GALAXY_URL
    else:
        msg = ('Failed to determine fetch method for content spec %s. '
               'Expecting a Galaxy name, SCM path, remote URL, path to a local '
               'archive file, or -e option and a directory path' % repository_spec_string)
        raise exceptions.GalaxyError(msg)
    return fetch_method


def resolve(data):
    src = data['src']
    if data['name'] is None:
        scm_name = repository_spec_parse.repo_url_to_repo_name(src)
        data['name'] = scm_name
        if '+' in src:
            (scm_url, scm_src) = src.split('+', 1)
            data['scm'] = scm_url
            data['src'] = scm_src

    # split the name on '.' and recombine the first 1 or 2
    name_parts = data['name'].split('.')
    new_name_parts = []
    new_name_parts.append(name_parts.pop(0))

    # we may not have a second part to the name
    try:
        new_name_parts.append(name_parts.pop(0))
    except IndexError:
        pass

    # combine the name parts, which may be one or two parts
    data['name'] = '.'.join(new_name_parts)

    return data


def editable_resolve(data):
    log.debug('data: %s', data)

    src = data['src']
    if src.startswith('/'):
        dir_name = os.path.basename(os.path.normpath(src))
        log.debug('dir_name: %s', dir_name)
        data['name'] = dir_name
    return data


def spec_data_from_string(repository_spec_string, namespace_override=None, fetch_method=None, editable=False):
    fetch_method = choose_repository_fetch_method(repository_spec_string, editable=editable)

    spec_data = repository_spec_parse.parse_string(repository_spec_string)
    spec_data['fetch_method'] = fetch_method

    log.debug('spec_data: %s', spec_data)

    resolved_data = {}

    if fetch_method == FetchMethods.GALAXY_URL:
        resolved_data = galaxy_repository_spec.resolve(spec_data)
    elif fetch_method == FetchMethods.EDITABLE:
        resolved_data = editable_resolve(spec_data)
    else:
        resolved_data = resolve(spec_data)

    log.debug('resolved_data: %s', resolved_data)
    spec_data.update(resolved_data)

    if namespace_override:
        if spec_data.get('namespace'):
            log.debug('using --namespace provided namespace "%s" to override detected namespace "%s"',
                      namespace_override,
                      spec_data['namespace'])
        else:
            log.debug('using --namespace provided namespace "%s" to since there was no namespace in "%s"',
                      namespace_override,
                      repository_spec_string)

        spec_data['namespace'] = namespace_override

    return spec_data


def repository_spec_from_string(repository_spec_string, namespace_override=None, editable=False):
    spec_data = spec_data_from_string(repository_spec_string, namespace_override=namespace_override, editable=editable)

    log.debug('spec_data: %s', spec_data)

    return RepositorySpec(name=spec_data.get('name'),
                          namespace=spec_data.get('namespace'),
                          version=spec_data.get('version'),
                          # version=version,
                          scm=spec_data.get('scm'),
                          spec_string=spec_data.get('spec_string'),
                          fetch_method=spec_data.get('fetch_method'),
                          src=spec_data.get('src'))
