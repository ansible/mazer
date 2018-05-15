import copy
import logging
import re
import six

from ansible_galaxy import exceptions
from ansible_galaxy.utils.content_name import repo_url_to_repo_name
from ansible_galaxy.utils.role_spec import role_spec_parse
from ansible_galaxy.models.content import VALID_ROLE_SPEC_KEYS

log = logging.getLogger(__name__)


def split_kwarg(spec_string, valid_keywords):
    if '=' not in spec_string:
        return (None, spec_string)

    parts = spec_string.split('=', 1)

    if parts[0] in valid_keywords:
        return (parts[0], parts[1])

    raise exceptions.GalaxyClientError('The content spec uses an unsuppoted keyword: %s' % spec_string)


def split_comma(spec_string, valid_keywords):
    # res = []
    comma_parts = spec_string.split(',')
    for comma_part in comma_parts:
        kw_parts = split_kwarg(comma_part, valid_keywords)
        log.debug('kw_parts: %s', kw_parts)
        yield kw_parts


def split_content_spec(spec_string, valid_keywords):
    comma_splitter = split_comma(spec_string, valid_keywords)

    info = {}
    for kw in valid_keywords:
        print('kw: %s' % kw)
        try:
            key, value = next(comma_splitter)
        except StopIteration:
            return info

        print('key=%s value=%s' % (key, value))
        if key:
            info[key] = value
        else:
            info[kw] = value

    return info


VERSION_WITH_LEADING_V_MATCH_RE = re.compile(r'^[vV]\d+\.')
VERSION_WITH_LEADING_V_SUB_RE = re.compile(r'(^[vV])')


def normalize_version_string(version_string):
    '''Normalize any version strings (rm 'v' from 'v1.0.0' for ex


    https://github.com/ansible/galaxy-cli/wiki/Content-Versioning#versions-in-galaxy-cli

    "When providing a version, provide the semantic version with or without the leading 'v' or 'V'."

    strip off leading v or V, and return a version string without it.'''

    if not version_string:
        return version_string

    matches = VERSION_WITH_LEADING_V_MATCH_RE.match(version_string)

    if not matches:
        return version_string

    new_versions_string = VERSION_WITH_LEADING_V_SUB_RE.sub('', version_string, 1)

    log.warn('Stripping leading "v" or "V" from version string "%s", new version string is  "%s"',
             version_string, new_versions_string)

    return new_versions_string


def parse_content_spec(content_spec_text, valid_keywords=None):
    '''Given a text/str object describing a galaxy content, parse it.

    And return a dict with keys: 'name', 'src', 'scm', 'version'
    '''

    valid_keywords = valid_keywords or ('src', 'version', 'name', 'scm')
    data = {'src': None,
            'name': None,
            'version': None,
            'scm': None}
    split_data = split_content_spec(content_spec_text, valid_keywords)

    data.update(split_data)

    if data['name'] is None:
        scm_name = repo_url_to_repo_name(data['src'])
        data['name'] = scm_name
        if '+' in data['src']:
            (scm_url, scm_src) = data['src'].split('+', 1)
            data['scm'] = scm_url
            data['src'] = scm_src

    data['version'] = normalize_version_string(data['version'])
    # log.debug('parsed content_spec_text="%s" into: %s', content_spec_text, data)
    return data


# FIXME: not really yaml,
# FIXME: whats the diff between this and role_spec_parse?
# TODO: return a new GalaxyContentMeta
# TODO: dont munge the passed in content
# TODO: split into smaller methods
# FIXME: does this actually use yaml?
# FIXME: kind of seems like this does two different things
# FIXME: letting this take a string _or_ a mapping seems troubleprone
def yaml_parse(content):
    """parses the passed in yaml string and returns a dict with name/src/scm/version

    Or... if the passed in 'content' is a dict, it either creates role or if not a role,
    it copies the dict and sets name/src/scm/version in it"""

    # FIXME: rm once we stop clobbering the passed in content, we can stop making a
    #        copy of orig_content as this is just for logging
    #        the original value

    if isinstance(content, six.string_types):
        log.debug('parsing content="%s" as a string', content)
        orig_content = copy.deepcopy(content)
        res = parse_content_spec(content)
        log.debug('parsed spec="%s" -> %s', content, res)
        return res

    log.debug('content="%s" is not a string (it is a %s) so we are assuming it is a dict',
              content, type(content))

    orig_content = copy.deepcopy(content)

    # Not sure what will/should happen if content is not a Mapping or a string
    # FIXME: if content is not a string or a dict/map, throw a reasonable error.
    #        for ex, if a list of strings is passed in, the content.copy() below throws
    #        an attribute error
    # FIXME: This isn't a 'parse' at all, if we want to convert a dict/map to the specific
    #        type of dict we expect, should be a different method
    # FIXME: what is expected to happen if passed an empty dict?
    if 'role' in content:
        log.debug('content="%s" appears to be a role', content)

        name = content['role']
        if ',' in name:
            # Old style: {role: "galaxy.role,version,name", other_vars: "here" }
            # Maintained for backwards compat
            content = role_spec_parse(content['role'])
        else:
            del content['role']
            content['name'] = name
    else:
        log.debug('content="%s" does not appear to be a role', content)

        # FIXME: just use a new name already
        # FIXME: this fails for objects with no dict attribute, like a list
        content_copy = content.copy()

        data = {'src': None, 'version': None, 'name': None, 'scm': None}
        data.update(content_copy)
        content = data

        if data.get('src', None):
            # valid_kw = ('src', 'version', 'name', 'scm')
            new_data = parse_content_spec(data['src'], VALID_ROLE_SPEC_KEYS)
            log.debug('new_data: %s', new_data)

            for key in new_data:
                if not data.get(key, None):
                    data[key] = new_data[key]

            # New style: { src: 'galaxy.role,version,name', other_vars: "here" }
            if 'github.com' in content["src"] and 'http' in content["src"] and '+' not in content["src"] and not content["src"].endswith('.tar.gz'):
                content["src"] = "git+" + content["src"]

        if 'version' not in content:
            content['version'] = ''

        if 'scm' not in content:
            content['scm'] = None

    for key in list(content.keys()):
        if key not in VALID_ROLE_SPEC_KEYS:
            log.debug('removing invalid key: %s', key)

            content.pop(key)

    log.debug('"parsed" content="%s" into: %s', orig_content, content)

    return content
