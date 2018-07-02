
import logging


log = logging.getLogger(__name__)

# TODO: use 'attr' or similar


class RepositoryNamespace(object):
    def __init__(self,
                 namespace=None,
                 path=None):
        self.namespace = namespace
        self.path = path

    def __repr__(self):
        return '%s(namespace="%s", path="%s")' % \
            (self.__class__.__name__,
             self.namespace,
             self.path)
