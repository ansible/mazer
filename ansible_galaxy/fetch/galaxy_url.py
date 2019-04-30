import logging

import semantic_version
from six.moves.urllib.parse import quote as urlquote

# mv details of this here
from ansible_galaxy import exceptions
from ansible_galaxy import download
from ansible_galaxy.fetch import base
# from ansible_galaxy.models.repository_spec import RepositorySpec
from ansible_galaxy.rest_api import GalaxyAPI

log = logging.getLogger(__name__)


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
        '''Find a collection

        This method does 3 things:

            1. Determine if the requested collection exists (GET /api/v2/collections/{namespace}/{name})
            2. Get the available versions (CollectionVersion) of the collection and
               select the "best" one. (GET /api/v2/collections/{namespace}/{name}/versions/)
            3. Get the details of the CollectionVersion including 'download_url' (GET /api/v2/collections/{namespace}/{names}/versions/{version}/,
               available as the 'href' in each CollectionVersion)

        It then returns the info about the Collection and CollectionVersion including download_url to be used by fetch()'''

        api = GalaxyAPI(self.galaxy_context)

        namespace = self.requirement_spec.namespace
        collection_name = self.requirement_spec.name

        log.debug('Querying %s for namespace=%s, name=%s', self.galaxy_context.server['url'], namespace, collection_name)

        # TODO: extract parsing of cli content sorta-url thing and add better tests

        # FIXME: Remove? We kind of need the actual Collection detail yet (ever?)
        collection_detail_url = '{base_api_url}/v2/collections/{namespace}/{name}/'.format(base_api_url=api.base_api_url,
                                                                                           namespace=urlquote(namespace),
                                                                                           name=urlquote(collection_name))

        log.debug('collection_detail_url: %s', collection_detail_url)

        collection_detail_data = api.get_object(href=collection_detail_url)

        if not collection_detail_data:
            raise exceptions.GalaxyClientError("- sorry, %s was not found on %s." % (self.requirement_spec.label,
                                                                                     api.api_server))

        versions_list_url = collection_detail_data.get('versions_url', None)

        # TODO: if versions ends up with a 'related' we could follow it instead of specific
        #       get_collection_version_list()
        # example results
        # [{
        #   "version": "2.4.5",
        #   "href": "/api/v2/collections/ansible/k8s/versions/2.4.5/",
        #  },
        #  {
        #   "version": "1.2.3",
        #   "href": "/api/v2/collections/ansible/k8s/versions/1.2.3/",
        #  }]
        log.debug('Getting collectionversions for %s.%s from %s',
                  namespace, collection_name, versions_list_url)

        collection_version_list_data = api.get_object(versions_list_url)

        log.debug('collectionvertlist data:\n%s', collection_version_list_data)

        if not collection_version_list_data:
            raise exceptions.GalaxyClientError("- sorry, %s was not found on %s." %
                                               (self.requirement_spec.label,
                                                api.api_server))

        collection_version_strings = [a.get('version') for a in collection_version_list_data if a.get('version', None)]

        # a Version() component of the CollectionVersion
        collection_versions_versions = [semantic_version.Version(ver) for ver in collection_version_strings]

        # No match returns None
        best_version = self.requirement_spec.version_spec.select(collection_versions_versions)

        # Find the rest of the info for the collectionversion that is the best version
        # linear search
        best_collectionversion = next(
            (cv for cv in collection_version_list_data
             # build a Version of both to for full semver matching
             if semantic_version.Version(cv['version']) == best_version),
            {})

        log.debug('best_collectionversion: %s', best_collectionversion)

        # We did not find a collection that meets this spec
        if not best_collectionversion:
            log.debug('Unable to find a collection that matches the spec: %s from available versions: %s',
                      self.requirement_spec,
                      [ver['version'] for ver in collection_version_list_data])
            raise exceptions.GalaxyCouldNotFindAnswerForRequirement('Unable to find a collection that matches the spec: %s' %
                                                                    self.requirement_spec.label,
                                                                    requirement_spec=self.requirement_spec)

        best_collectionversion_detail_data = api.get_object(href=best_collectionversion.get('href', None))

        download_url = best_collectionversion_detail_data.get('download_url', None)

        log.debug('download_url for %s.%s: %s', namespace, collection_name, download_url)

        if not download_url:
            raise exceptions.GalaxyError('no external_url info on the Repository object from %s' % self.requirement_spec.label)

        # collectionversion_metadata = best_collectionversion_detail_data.get('metadata', None)
        # log.debug('collectionversion_metadata: %s', collectionversion_metadata)

        # TODO: raise exceptions if API requests are empty

        results = {'content': {'galaxy_namespace': namespace,
                               'repo_name': collection_name,
                               'version': best_version},
                   'custom': {'download_url': download_url},
                   }

        return results

    def fetch(self, find_results=None):
        find_results = find_results or {}

        results = {}

        download_url = find_results['custom']['download_url']

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
                   'fetch_method': self.fetch_method}

        # So fetch_results has the download url, if we follow redirects
        # we could also add a 'final_download_url' or 'downloaded_url' so
        # we know the original and the final url after redirects
        results['custom'] = find_results['custom']
        results['content'] = find_results['content']

        return results
