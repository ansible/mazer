import copy
import logging
import six

from ansible_galaxy import content_spec_parse
# from ansible_galaxy import content_spec
from ansible_galaxy.utils.role_spec import role_spec_parse
from ansible_galaxy.models.content import VALID_ROLE_SPEC_KEYS


log = logging.getLogger(__name__)


# FIXME: not really yaml,
# FIXME: whats the diff between this and role_spec_parse?
# TODO: return a new GalaxyContentMeta
# TODO: dont munge the passed in content
# TODO: split into smaller methods
# FIXME: does this actually use yaml?
# FIXME: kind of seems like this does two different things
# FIXME: letting this take a string _or_ a mapping seems troubleprone
def yaml_parse(content, resolver=None):
    """parses the passed in yaml string and returns a dict with name/src/scm/version

    Or... if the passed in 'content' is a dict, it either creates role or if not a role,
    it copies the dict and sets name/src/scm/version in it"""

    # FIXME: rm once we stop clobbering the passed in content, we can stop making a
    #        copy of orig_content as this is just for logging
    #        the original value

    if isinstance(content, six.string_types):
        log.debug('parsing content="%s" as a string', content)
        orig_content = copy.deepcopy(content)
        res = content_spec_parse.spec_data_from_string(content, resolver=resolver)
        # res = content_spec_parse.parse_string(content)
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
            # new_data = content_spec_parse.parse_string(data['src'], VALID_ROLE_SPEC_KEYS)
            new_data = content_spec_parse.spec_data_from_string(data['src'], resolver=resolver)
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
        # sub_name doesnt mean anything to role spec
        if key not in VALID_ROLE_SPEC_KEYS and key not in ('sub_name', 'namespace'):
            log.debug('removing invalid key: %s', key)

            content.pop(key)

    log.debug('"parsed" content="%s" into: %s', orig_content, content)

    return content
