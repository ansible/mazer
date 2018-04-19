"""Exceptions used by ansible_galaxy client library"""


class GalaxyError(Exception):
    """Base exception for ansible_galaxy client library"""
    pass


class ParserError(GalaxyError):
    """Base exception raised for errors while parsing galaxy content"""
    pass
