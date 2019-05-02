"""Exceptions used by ansible_galaxy client library"""

import requests


class GalaxyError(Exception):
    """Base exception for ansible_galaxy library and ansible_galaxy_cli app"""
    pass


class GalaxyClientError(GalaxyError):
    """Base exception for ansible_galaxy library

    Exceptions that escape from ansible_galaxy. should be based on this class"""
    pass


class ParserError(GalaxyError):
    """Base exception raised for errors while parsing galaxy content"""
    pass


# TODO: attrs for http code, url, msg or just reuse http exception from elsewhere
class GalaxyDownloadError(GalaxyError):
    '''Raise when there is an error downloading galaxy content'''

    def __init__(self, *args, **kwargs):
        url = kwargs.pop('url', None)
        super(GalaxyDownloadError, self).__init__(*args, **kwargs)
        self.url = url

    def __str__(self):
        url_blurb = ': '
        if self.url:
            url_blurb = ' (%s): ' % self.url
        msg = 'Error downloading%s%s' % (url_blurb, super(GalaxyDownloadError, self).__str__())
        return msg

    def __repr__(self):
        return '%s(url=%s, %s)' % (self.__class__.__name__, self.url, self.args)


class GalaxyRepositorySpecError(GalaxyClientError):
    '''Raised if the repository_spec was invalid'''
    def __init__(self, *args, **kwargs):
        repository_spec = kwargs.pop('repository_spec', None)
        super(GalaxyRepositorySpecError, self).__init__(*args, **kwargs)
        self.repository_spec = repository_spec


class GalaxyCouldNotFindAnswerForRequirement(GalaxyClientError):
    '''Raised if a fetch.find() can not find a collection that meets the requirement spec'''
    def __init__(self, *args, **kwargs):
        requirement_spec = kwargs.pop('requirement_spec', None)
        super(GalaxyCouldNotFindAnswerForRequirement, self).__init__(*args, **kwargs)
        self.requirement_spec = requirement_spec


class GalaxyRequestsError(GalaxyError):
    """Base exception for ansible_galaxy exceptions that wrap requests.RequestException"""
    pass


class GalaxyRestServerError(requests.RequestException, GalaxyRequestsError):
    '''Raised if the REST API http server returns an http server error

    ie, the server response has a http status code indicating an error
    but the response does not contain a json formatted error message.

    For example, a 500 error that returns a plain text body is a
    server error, but not a Galaxy API error.'''
    pass


class GalaxyRestAPIError(requests.HTTPError, GalaxyRequestsError):
    '''Raised if there were errors returned from the Galaxy REST API'''

    def __init__(self, *args, **kwargs):
        error_data = kwargs.pop('error_data', {}) or {}

        super(GalaxyRestAPIError, self).__init__(*args, **kwargs)

        self.error_data = error_data

        self.code = error_data.get('code', 'unknown_api_error')
        self.message = error_data.get('message', 'A Galaxy REST API error.')
        self.errors = error_data.get('errors', [])

    # TODO: repr/str to format error_data 'code', 'message' and 'error' fields


class GalaxyRestAPIClientRequestError(requests.RequestException, GalaxyRequestsError):
    '''Raised if there is an error while making a http rest api request

    ie, requests.ConnectionError, requests.Timeout, etc.
    This should not be raised if the server responded with a http response
    with an error status code. Use GalaxyRestAPIError for that.'''
    pass


class GalaxyClientAPIConnectionError(requests.ConnectionError, GalaxyRequestsError):
    '''Raised if there were errors connecting to the Galaxy REST API'''
    pass


# TODO: proper rst docstrings with api info
class GalaxyConfigFileError(GalaxyClientError):
    '''Raised where there is an error loading or parsing a config file

       has a 'config_file_path' attribute with the config file path'''

    def __init__(self, *args, **kwargs):
        config_file_path = kwargs.pop('config_file_path', None)
        super(GalaxyConfigFileError, self).__init__(*args, **kwargs)
        self.config_file_path = config_file_path


class GalaxyArchiveError(GalaxyClientError):
    '''Raised for errors related to content archive (tar) files'''

    def __init__(self, *args, **kwargs):
        archive_path = kwargs.pop('archive_path', None)
        super(GalaxyArchiveError, self).__init__(*args, **kwargs)
        self.archive_path = archive_path


class GalaxyPublishError(GalaxyClientError):
    ''' Raised for errors related to publish command '''

    def __init__(self, msg, *args, **kwargs):
        self.msg = msg
        self.archive_path = kwargs.pop('archive_path', None)
        self.url = kwargs.pop('url', '')
        super(GalaxyPublishError, self).__init__(*args, **kwargs)

    def __str__(self, *args, **kwargs):
        msg = 'Error publishing %s to %s - %s' % (self.archive_path, self.url, self.msg)
        return msg
