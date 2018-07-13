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
        log.debug('self.names: %s other.content_spec.name: %s', self.names, other.content_spec.name)
        return other.content_spec.name in self.names


class MatchLabels(Match):
    def __init__(self, labels):
        self.labels = labels

    def match(self, other):
        log.debug('self.labels: %s other.label: %s', self.labels, other.content_spec.label)
        return other.content_spec.label in self.labels


class MatchContentSpec(Match):
    def __init__(self, content_specs):
        self.content_specs = content_specs or []

    def match(self, other):
        # log.debug('is %s in %s', other.content_spec, self.content_specs)
        return other.content_spec in self.content_specs


class MatchNamespacesOrLabels(Match):
    def __init__(self, namespaces_or_labels):
        self.namespaces_or_labels = namespaces_or_labels or []

    def match(self, other):
        log.debug('self.namespaces_or_labels: %s other.namespace: %s other.label: %s',
                  self.namespaces_or_labels, other.content_spec.namespace, other.content_spec.label)
        # TODO: should this matcher require a namespace string or a namespace object? either?
        return any([other.content_spec.label in self.namespaces_or_labels,
                    other.content_spec.namespace in self.namespaces_or_labels])
