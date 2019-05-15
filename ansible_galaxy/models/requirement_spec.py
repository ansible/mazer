import logging

import attr
import semantic_version

from ansible_galaxy.utils.version import convert_string_to_version_spec, version_needs_aka, \
    normalize_version_string

log = logging.getLogger(__name__)


@attr.s(frozen=True)
class RequirementSpec(object):
    '''The info used to identify a requirement.

    ie, the namespace, name, and the spec of what version is
    required'''

    namespace = attr.ib()
    name = attr.ib()
    version_spec = attr.ib(type=semantic_version.Spec, default=semantic_version.Spec('*'),
                           converter=convert_string_to_version_spec)

    # This is for supporting 'v1.0.0' etc. In that case the version_spec is '==1.0.0' and
    # version_aka is 'v1.0.0'. Need to track it because it is used to build github download
    # urls sometimes
    version_aka = attr.ib(default=None)
    fetch_method = attr.ib(default=None, cmp=False)
    src = attr.ib(default=None, cmp=False)
    scm = attr.ib(default=None, cmp=False)

    # If created from a parsed string, spec_string is copy of the full string
    spec_string = attr.ib(default=None, cmp=False)

    @property
    def label(self):
        return '%s.%s (version_spec: %s)' % (self.namespace, self.name, str(self.version_spec))

    @classmethod
    def from_dict(cls, data):
        version_spec_str = data.get('version_spec', None)

        # If we are specifying a version in the spec_data, then
        # assume we want to install exactly that version, so build
        # a version_spec to indicate that (ie, '==1.0.0' etc)
        if not version_spec_str:
            if data.get('version', None):
                ver = data['version']

                # try to handle matching 'v1.0.0' etc
                if version_needs_aka(str(ver)):
                    data['version'] = normalize_version_string(ver)
                    data['version_aka'] = ver
                version_spec_str = data['version']
            else:
                # No version_spec, and version is None, that means match anything
                version_spec_str = '*'

        instance = cls(namespace=data['namespace'],
                       name=data['name'],
                       version_spec=version_spec_str,
                       version_aka=data.get('version_aka', None),
                       fetch_method=data.get('fetch_method', None),
                       scm=data.get('scm', None),
                       spec_string=data.get('spec_string', None),
                       src=data.get('src', None),
                       )
        return instance
