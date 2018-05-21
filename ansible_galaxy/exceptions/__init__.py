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
    pass


class GalaxyClientAPIConnectionError(GalaxyClientError):
    '''Raised if there were errors connecting to the Galaxy REST API'''
    pass


class GalaxyConfigError(GalaxyClientError):
    '''Raised if there is an error parsing the configuration files'''
    pass
