import logging

from ansible_galaxy import repository_spec_parse

from ansible_galaxy.models.repository_spec import RepositorySpec


log = logging.getLogger(__name__)


def repository_spec_from_string(repository_spec_string, namespace_override=None, editable=False):
    spec_data = repository_spec_parse.spec_data_from_string(repository_spec_string, namespace_override=namespace_override, editable=editable)

    log.debug('spec_data: %s', spec_data)

    return RepositorySpec(name=spec_data.get('name'),
                          namespace=spec_data.get('namespace'),
                          version=spec_data.get('version'),
                          # version=version,
                          scm=spec_data.get('scm'),
                          spec_string=spec_data.get('spec_string'),
                          fetch_method=spec_data.get('fetch_method'),
                          src=spec_data.get('src'))
