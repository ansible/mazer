
import logging


# mv details of this here
from ansible_galaxy import exceptions
from ansible_galaxy import download
from ansible_galaxy.fetch import base
# from ansible_galaxy.models.repository_spec import RepositorySpec
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


# TODO: split into galaxy_role/galaxy_collection ?
class GalaxyUrlFetch(base.BaseFetch):
    fetch_method = 'galaxy_url'

    def __init__(self, galaxy_context, requirement_spec):
        super(GalaxyUrlFetch, self).__init__()

        self.requirement_spec = requirement_spec
        self.galaxy_context = galaxy_context

        self.validate_certs = not self.galaxy_context.server['ignore_certs']

        log.debug('requirement_spec: %s', requirement_spec)
        # log.debug('Validate TLS certificates: %s', self.validate_certs)

    def find(self):
        api = GalaxyAPI(self.galaxy_context)

        namespace = self.requirement_spec.namespace
        repo_name = self.requirement_spec.name

        log.debug('Querying %s for namespace=%s, name=%s', self.galaxy_context.server['url'], namespace, repo_name)

        # TODO: extract parsing of cli content sorta-url thing and add better tests

        # FIXME: exception handling
        repo_data = api.lookup_repo_by_name(namespace, repo_name)

        if not repo_data:
            raise exceptions.GalaxyClientError("- sorry, %s was not found on %s." % (self.requirement_spec.label,
                                                                                     api.api_server))

        # FIXME - Need to update our API calls once Galaxy has them implemented
        related = repo_data.get('related', {})

        repo_versions_url = related.get('versions', None)

        # FIXME: exception handling
        repoversions = api.fetch_content_related(repo_versions_url)

        content_repo_versions = [a.get('version') for a in repoversions if a.get('version', None)]

        repo_version_best = repository_version.get_repository_version(repo_data,
                                                                      requirement_spec=self.requirement_spec,
                                                                      repository_versions=content_repo_versions)

        # get the RepositoryVersion obj (or its data anyway)
        _repoversion = select_repository_version(repoversions, repo_version_best)

        # Note: download_url can point anywhere...
        external_url = repo_data.get('external_url', None)

        if not external_url:
            raise exceptions.GalaxyError('no external_url info on the Repository object from %s' % self.requirement_spec.label)

        results = {'content': {'galaxy_namespace': namespace,
                               'repo_name': repo_name,
                               'version': _repoversion.get('version')},
                   'requirement_spec_version_spec': self.requirement_spec.version_spec,
                   'custom': {'external_url': external_url,
                              'repo_data': repo_data,
                              'repoversion': _repoversion,
                              },
                   }

        return results

    def fetch(self, find_results=None):
        find_results = find_results or {}

        results = {}

        download_url = get_download_url(repo_data=find_results['custom']['repo_data'],
                                        external_url=find_results['custom']['external_url'],
                                        repoversion=find_results['custom']['repoversion'])

        # download_url = _build_download_url(external_url=external_url, version=_content_version)
        # TODO: error handling if there is no download_url

        log.debug('repository_spec=%s', self.requirement_spec)
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
