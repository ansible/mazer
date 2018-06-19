import logging

log = logging.getLogger(__name__)


# TODO: abc?
class Match(object):
    def __call__(self, other):
        return self.match(other)

    def match(self, other):
        return True


class MatchAll(Match):
    def match(self, other):
        return True


class MatchNone(Match):
    def match(self, other):
        return False


class MatchNames(Match):
    def __init__(self, names):
        self.names = names

    def match(self, other):
        log.debug('self.names: %s other.name: %s', self.names, other.name)
        return other.name in self.names


class MatchLabels(Match):
    def __init__(self, labels):
        self.labels = labels

    def match(self, other):
        log.debug('self.labels: %s other.label: %s', self.labels, other.label)
        return other.label in self.labels


class MatchNamespacesOrLabels(Match):
    def __init__(self, namespaces_or_labels):
        self.namespaces_or_labels = namespaces_or_labels or []

    def match(self, other):
        log.debug('self.namespaces_or_labels: %s other.namespace: %s other.label: %s', self.namespaces_or_labels, other.namespace, other.label)
        return any([other.label in self.namespaces_or_labels,
                    other.namespace in self.namespaces_or_labels])
