
class ContentSpec(object):
    '''The info used to identify and reference a galaxy content.

    For ex, 'testing.ansible-testing-content' will result in
    a ContentSpec(name=ansible-testing-content, repo=ansible-testing-content,
                  namespace=testing, raw=testing.ansible-testing-content)'''

    def __init__(self,
                 name=None,
                 namespace=None,
                 spec_string=None,
                 src=None,       # FIXME: rm
                 repo=None,
                 version=None,
                 scm=None,
                 fetch_method=None):
        self.name = name
        self.namespace = namespace
        self.spec_string = spec_string
        self.repo = repo
        self.version = version
        self.scm = scm
        self.src = src
        self.fetch_method = fetch_method

    def __eq__(self, other):
        return (self.name, self.namespace, self.version, self.scm) == \
            (other.name, other.namespace, other.version, other.scm)

    def __repr__(self):
        format_ = 'ContentSpec(name=%s, namespace=%s, version=%s, src=%s, scm=%s, spec_string=%s, fetch_method=%s)'

        return format_ % (self.name, self.namespace, self.version, self.src,
                          self.scm, self.spec_string, self.fetch_method)

    def _as_dict(self):
        return {'name': self.name,
                'namespace': self.namespace,
                'version': self.version,
                'repo': self.repo,
                'spec_string': self.spec_string,
                'fetch_method': self.fetch_method,
                'src': self.src,
                }

    @property
    def data(self):
        return self._as_dict()
