import logging

from ansible_galaxy import exceptions

log = logging.getLogger(__name__)


def resolve(spec_data):
    # build up the 'name.namespace' spec based
    # split the name on '.' and recombine the first 1 or 2
    src = spec_data['src']
    name_parts = src.split('.')

    # enforce the galaxy content spec specific rule about requiring a dot in namespace.name

    # if we have namespace.name, pop off namespace and use rest for name
    if len(name_parts) < 2:
        raise exceptions.GalaxyError('A galaxy content spec must have at least a namespace, a dot, and a name but "%s" does not.'
                                     % spec_data.get('spec_string'))

    if len(name_parts) > 1:
        spec_data['namespace'] = name_parts[0]

        # use the second part of namespace.name if there wasnt an explicit name=foo
        if not spec_data['name']:
            spec_data['name'] = name_parts[1]
    else:
        spec_data['name'] = name_parts[0]

    return spec_data
