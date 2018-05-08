
import logging

# mv details of this here
from ansible_galaxy import exceptions
from ansible_galaxy import download
from ansible_galaxy.fetch import base
from ansible_galaxy.flat_rest_api.api import GalaxyAPI
from ansible_galaxy.models import content_version
from ansible_galaxy.utils.content_name import parse_content_name

log = logging.getLogger(__name__)


def _build_download_url(external_url=None, version=None):
    if external_url and version:
        archive_url = '%s/archive/%s.tar.gz' % (external_url, version)
        return archive_url


class GalaxyUrlFetch(base.BaseFetch):
    fetch_method = 'galaxy_url'

    def __init__(self, content_spec, content_version,
                 galaxy_context, validate_certs=None):
        super(GalaxyUrlFetch, self).__init__()

        # self.galaxy_url = galaxy_url
        self.content_spec = content_spec
        self.content_version = content_version
        self.galaxy_context = galaxy_context

        self.validate_certs = validate_certs
        if validate_certs is None:
            self.validate_certs = True

    def fetch(self):
        api = GalaxyAPI(self.galaxy_context)

        # FIXME - Need to update our API calls once Galaxy has them implemented
        content_username, repo_name, content_name = parse_content_name(self.content_spec)

        log.debug('content_username=%s, repo_name=%s content_name=%s', content_username, repo_name, content_name)

        # TODO: extract parsing of cli content sorta-url thing and add better tests
        repo_name = repo_name or content_name

        # FIXME: exception handling
        content_data = api.lookup_content_repo_by_name(content_username, repo_name)

        if not content_data:
            raise exceptions.GalaxyClientError("- sorry, %s was not found on %s." % (self.content_spec,
                                                                                     api.api_server))

        if content_data.get('role_type') == 'APP':
            # Container Role
            self.display_callback("%s is a Container App role, and should only be installed using Ansible "
                                  "Container" % content_name, level='warning')

        # FIXME - Need to update our API calls once Galaxy has them implemented
        related = content_data.get('related', {})
        related_versions_url = related.get('versions', None)

        # FIXME: exception handling
        content_versions = api.fetch_content_related(related_versions_url)

        log.debug('content_versions: %s', content_versions)

        related_repo_url = related.get('repository', None)
        content_repo = None
        if related_repo_url:
            content_repo = api.fetch_content_related(related_repo_url)
        # log.debug('content_repo: %s', content_repo)
        # FIXME: mv to it's own method
        # FIXME: pass these to fetch() if it really needs it
        _content_version = content_version.get_content_version(content_data,
                                                               version=self.content_version,
                                                               content_versions=content_versions,
                                                               content_content_name=content_name)

        # FIXME: stop munging state
        # self.content_meta.version = _content_version

        external_url = content_repo.get('external_url', None)
        if not external_url:
            raise exceptions.GalaxyError('no external_url info on the Repository object from %s',
                                         related_repo_url)

        download_url = _build_download_url(external_url=external_url, version=_content_version)

        log.debug('content_spec=%s download_url=%s', self.content_spec, download_url)

        try:
            content_archive_path = download.fetch_url(download_url,
                                                      validate_certs=self.validate_certs)
        except exceptions.GalaxyDownloadError as e:
            log.exception(e)
            self.display_callback("failed to download the file: %s" % str(e))
            return None

        self.local_path = content_archive_path

        log.debug('content_archive_path=%s', content_archive_path)

        return content_archive_path
