
import attr


@attr.s(frozen=True)
class ContentItem(object):
    '''A content item from a collection, for ex a role or plugin.

    For ex, 'testing.ansible-testing-content' will have multiple content
    items. One for each role or type of plugins.
    '''
    namespace = attr.ib()
    name = attr.ib()

    content_item_type = attr.ib(default=None)
    version = attr.ib(default=None)
    path = attr.ib(default=None)

    @property
    def label(self):
        return '%s.%s' % (self.namespace, self.name)
