
import logging

# mv details of this here
from ansible_galaxy import exceptions
from ansible_galaxy import download
from ansible_galaxy.fetch import base
from ansible_galaxy.models.repository_spec import RepositorySpec
from ansible_galaxy.rest_api import GalaxyAPI
from ansible_galaxy import repository_version

log = logging.getLogger(__name__)


def get_download_url(repo_data=None, external_url=None, repoversion=None):
    repo_data = repo_data or {}

    # If we want a specific version, provide an exact match repoversion.
    # if provided an exact match repoversion, use its download_url
    if 'download_url' in repoversion:
        return repoversion['download_url']

    # but then try whatever the Repository suggests for download_url
    # This should be the case if we dont specify a version and the galaxy Repository
    # has no versions associated to it, so this will likely reference the latest in
    # the default branch
    if 'download_url' in repo_data:
        return repo_data['download_url']

    # server response didn't suggest a download_url, take a guess and make one up
    if external_url and repoversion:
        archive_url = '%s/archive/%s.tar.gz' % (external_url, repoversion['version'])
        return archive_url


def select_repository_version(repoversions, version):
    # repoversion's 'version' is 'not null' so should always exist
    # however, the list of repoversions can be empty

    # If the rest api returns a empty list for repo versions, return an
    # empty dict for 'no version'
    if not repoversions:
        return {}

    # we could build a map/dict first and search in it, but we only use this
    # once, so this linear search is ok, since building the map would be that
    # plus the getitem
    results = [x for x in repoversions if x['version'] == version]

    # no matching versions, return an empty dict
    # TODO: raise VersionNotFoundError ? return some sort of NullRepositoryVersion instance?
    if not results:
        return {}

    # repoversions is uniq on (version, repo.id) so for any given repo,
    # there should only be one result here
    repoversion = results.pop()
    return repoversion


class GalaxyUrlFetch(base.BaseFetch):
    fetch_method = 'galaxy_url'

    def __init__(self, repository_spec, galaxy_context):
        super(GalaxyUrlFetch, self).__init__()

        self.repository_spec = repository_spec
        self.galaxy_context = galaxy_context

        self.validate_certs = not self.galaxy_context.server['ignore_certs']

        log.debug('repository_spec: %s', repository_spec)
        # log.debug('Validate TLS certificates: %s', self.validate_certs)

    def find(self):
        api = GalaxyAPI(self.galaxy_context)

        namespace = self.repository_spec.namespace
        repo_name = self.repository_spec.name

        log.debug('Querying %s for namespace=%s, name=%s', self.galaxy_context.server['url'], namespace, repo_name)

        # TODO: extract parsing of cli content sorta-url thing and add better tests

        # FIXME: exception handling
        repo_data = api.lookup_repo_by_name(namespace, repo_name)

        if not repo_data:
            raise exceptions.GalaxyClientError("- sorry, %s was not found on %s." % (self.repository_spec.label,
                                                                                     api.api_server))

        # FIXME - Need to update our API calls once Galaxy has them implemented
        related = repo_data.get('related', {})

        repo_versions_url = related.get('versions', None)

        log.debug('related=%s', related)

        # FIXME: exception handling
        repoversions = api.fetch_content_related(repo_versions_url)

        content_repo_versions = [a.get('version') for a in repoversions if a.get('version', None)]

        # FIXME: mv to it's own method
        # FIXME: pass these to fetch() if it really needs it
        repo_version_best = repository_version.get_repository_version(repo_data,
                                                                      version=self.repository_spec.version,
                                                                      repository_versions=content_repo_versions,
                                                                      content_content_name=self.repository_spec.name)

        # get the RepositoryVersion obj (or its data anyway)
        _repoversion = select_repository_version(repoversions, repo_version_best)

        # external_url isnt specific, it could be something like github.com/alikins/some_collection
        # external_url is the third option after a 'download_url' provided by the galaxy rest API
        # (repo version specific download_url first if applicable, then the general download_url)
        # Note: download_url can point anywhere...
        external_url = repo_data.get('external_url', None)

        if not external_url:
            raise exceptions.GalaxyError('no external_url info on the Repository object from %s' % self.repository_spec.label)

        # The repo spec of the install candidate with potentially a different version
        potential_repository_spec = RepositorySpec(namespace=namespace,
                                                   name=repo_name,
                                                   version=_repoversion['version'],
                                                   fetch_method=self.repository_spec.fetch_method,
                                                   scm=self.repository_spec.scm,
                                                   spec_string=self.repository_spec.spec_string,
                                                   src=self.repository_spec.src)

        results = {'content': {'galaxy_namespace': namespace,
                               'repo_name': repo_name},
                   'specified_content_version': self.repository_spec.version,
                   'specified_repository_spec': self.repository_spec,
                   'custom': {'content_repo_versions': content_repo_versions,
                              'external_url': external_url,
                              'galaxy_context': self.galaxy_context,
                              'related': related,
                              'repo_data': repo_data,
                              'repo_versions_url': repo_versions_url,
                              'repoversion': _repoversion,
                              'potential_repository_spec': potential_repository_spec},
                   }

        return results

    def fetch(self, find_results=None):
        # log.debug('fetch: find_results: %s', find_results)
        find_results = find_results or {}

        results = {}

        download_url = get_download_url(repo_data=find_results['custom']['repo_data'],
                                        external_url=find_results['custom']['external_url'],
                                        repoversion=find_results['custom']['repoversion'])

        # download_url = _build_download_url(external_url=external_url, version=_content_version)
        # TODO: error handling if there is no download_url

        log.debug('repository_spec=%s', self.repository_spec)
        log.debug('download_url=%s', download_url)

        # for including in any error messages or logging for this fetch
        self.remote_resource = download_url

        # can raise GalaxyDownloadError
        repository_archive_path = download.fetch_url(download_url,
                                                     validate_certs=self.validate_certs)

        self.local_path = repository_archive_path

        log.debug('repository_archive_path=%s', repository_archive_path)

        # TODO: This is indication that a fetcher is wrong abstraction. A fetch
        #       can resolve a name/spec, find metadata about the content including avail versions,
        #       compare/sort versions, select matching versions, find a download uri, and finally
        #       actually fetch it.
        #       Ie, more of a RepositoryRepository (aiee) (RepositorySource? RepositoryChannel? RepositoryProvider?)
        #       that is a remote 'channel' with info and content itself.
        results = {'archive_path': repository_archive_path,
                   'download_url': download_url,
                   'fetch_method': self.fetch_method}

        results['custom'] = {}
        results['content'] = find_results['content']
        results['content']['fetched_version'] = find_results['custom']['repoversion'].get('version')

        return results
