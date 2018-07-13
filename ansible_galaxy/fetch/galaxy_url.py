
import logging

# mv details of this here
from ansible_galaxy import exceptions
from ansible_galaxy import download
from ansible_galaxy.fetch import base
from ansible_galaxy.rest_api import GalaxyAPI
from ansible_galaxy import content_version
from ansible_galaxy.utils.content_name import parse_content_name

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
    # repository_version's 'version' is 'not null' so should always exist
    # however, the list of repository_versions can be empty

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

    # repository_versions is uniq on (version, repo.id) so for any given repo,
    # there should only be one result here
    repoversion = results.pop()
    return repoversion


class GalaxyUrlFetch(base.BaseFetch):
    fetch_method = 'galaxy_url'

    def __init__(self, content_spec, content_version,
                 galaxy_context):
        super(GalaxyUrlFetch, self).__init__()

        # self.galaxy_url = galaxy_url
        self.content_spec = content_spec
        self.content_version = content_version
        self.galaxy_context = galaxy_context

        self.validate_certs = not self.galaxy_context.server['ignore_certs']

        # log.debug('Validate TLS certificates: %s', self.validate_certs)

    def find(self):
        api = GalaxyAPI(self.galaxy_context)

        # FIXME - Need to update our API calls once Galaxy has them implemented
        content_username, repo_name, content_name = parse_content_name(self.content_spec)

        log.debug('Querying %s for namespace=%s, name=%s', self.galaxy_context.server['url'], content_username, repo_name)

        # TODO: extract parsing of cli content sorta-url thing and add better tests
        repo_name = repo_name or content_name

        # FIXME: exception handling
        repo_data = api.lookup_repo_by_name(content_username, repo_name)

        if not repo_data:
            raise exceptions.GalaxyClientError("- sorry, %s was not found on %s." % (self.content_spec,
                                                                                     api.api_server))

        # FIXME: ?
        # if repo_data.get('role_type') == 'APP#':
            # Container Role
        #    self.display_callback("%s is a Container App role, and should only be installed using Ansible "
        #                          "Container" % content_name, level='warning')

        # FIXME - Need to update our API calls once Galaxy has them implemented
        related = repo_data.get('related', {})

        repo_versions_url = related.get('versions', None)

        log.debug('related=%s', related)

        # FIXME: exception handling
        repoversions = api.fetch_content_related(repo_versions_url)

        # related_repo_url = related.get('repository', None)
        # log.debug('related_repo_url: %s', related_repo_url)
        # related_content_url = related.get('content', None)
        # log.debug('related_content_url: %s', related_content_url)

        # content_repo = None
        # if related_content_url:
        #     content_repo = api.fetch_content_related(related_content_url)
        content_repo_versions = [a.get('version') for a in repoversions if a.get('version', None)]

        # log.debug('content_repo: %s', content_repo)
        # FIXME: mv to it's own method
        # FIXME: pass these to fetch() if it really needs it
        repo_version_best = content_version.get_content_version(repo_data,
                                                                version=self.content_version,
                                                                content_versions=content_repo_versions,
                                                                content_content_name=content_name)

        # get the RepositoryVersion obj (or its data anyway)
        _repoversion = select_repository_version(repoversions, repo_version_best)
        # FIXME: stop munging state
        # self.content_meta.version = _content_version

        external_url = repo_data.get('external_url', None)
        if not external_url:
            raise exceptions.GalaxyError('no external_url info on the Repository object from %s' % repo_name)

        results = {'content': {'galaxy_namespace': content_username,
                               'repo_name': repo_name,
                               'content_name': content_name},
                   'specified_content_version': self.content_version,
                   'specified_content_spec': self.content_spec,
                   'custom': {'content_repo_versions': content_repo_versions,
                              'external_url': external_url,
                              'galaxy_context': self.galaxy_context,
                              'related': related,
                              'repo_data': repo_data,
                              'repo_versions_url': repo_versions_url,
                              'repoversion': _repoversion},
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

        log.debug('content_spec=%s', self.content_spec)
        log.debug('download_url=%s', download_url)

        # for including in any error messages or logging for this fetch
        self.remote_resource = download_url

        # can raise GalaxyDownloadError
        content_archive_path = download.fetch_url(download_url,
                                                  validate_certs=self.validate_certs)

        self.local_path = content_archive_path

        log.debug('content_archive_path=%s', content_archive_path)

        # TODO: This is indication that a fetcher is wrong abstraction. A fetch
        #       can resolve a name/spec, find metadata about the content including avail versions,
        #       compare/sort versions, select matching versions, find a download uri, and finally
        #       actually fetch it.
        #       Ie, more of a 'ContentRepository' (ContentSource? ContentChannel? ContentProvider?)
        #       that is a remote 'channel' with info and content itself.
        results = {'archive_path': content_archive_path,
                   'download_url': download_url,
                   'fetch_method': self.fetch_method}

        results['custom'] = {}
        results['content'] = find_results['content']
        results['content']['fetched_version'] = find_results['custom']['repoversion'].get('version')

        return results
