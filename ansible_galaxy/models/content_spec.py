import attr


@attr.s(frozen=True)
class ContentSpec(object):
    '''The info used to identify and reference a galaxy content.

    For ex, 'testing.ansible-testing-content' will result in
    a ContentSpec(name=ansible-testing-content, repo=ansible-testing-content,
                  namespace=testing, raw=testing.ansible-testing-content)'''
    namespace = attr.ib()
    name = attr.ib()
    version = attr.ib(default=None)

    # only namespace/name/version are used for eq checks
    fetch_method = attr.ib(default=None, cmp=False)
    scm = attr.ib(default=None, cmp=False)
    spec_string = attr.ib(default=None, cmp=False)
    src = attr.ib(default=None, cmp=False)

    @property
    def label(self):
        return '%s.%s' % (self.namespace, self.name)
