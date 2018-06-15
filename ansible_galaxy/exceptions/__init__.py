"""Exceptions used by ansible_galaxy client library"""


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


class GalaxyContentSpecError(GalaxyClientError):
    '''Raised if the content_spec was invalid'''
    def __init__(self, *args, **kwargs):
        content_spec = kwargs.pop('content_spec', None)
        super(GalaxyContentSpecError, self).__init__(*args, **kwargs)
        self.content_spec = content_spec


class GalaxyClientAPIConnectionError(GalaxyClientError):
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
