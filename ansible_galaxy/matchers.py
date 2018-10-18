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
        log.debug('self.names: %s other.repository_spec.name: %s', self.names, other.repository_spec.name)
        return other.repository_spec.name in self.names


class MatchLabels(Match):
    def __init__(self, labels):
        self.labels = labels

    def match(self, other):
        log.debug('self.labels: %s other.label: %s', self.labels, other.repository_spec.label)
        return other.repository_spec.label in self.labels


class MatchContentSpec(Match):
    def __init__(self, repository_specs):
        self.repository_specs = repository_specs or []

    def match(self, other):
        log.debug('is %s in %s', other.repository_spec, self.repository_specs)
        return other.repository_spec in self.repository_specs


class MatchContentSpecsNamespaceNameVersion(Match):
    def __init__(self, repository_specs):
        self.namespaces_names_versions = [(x.namespace, x.name, x.version) for x in repository_specs] or []

    def match(self, other):
        log.debug('is %s in %s', (other.repository_spec.namespace, other.repository_spec.name, other.repository_spec.version), self.namespaces_names_versions)
        return (other.repository_spec.namespace, other.repository_spec.name, other.repository_spec.version) in self.namespaces_names_versions


class MatchNamespacesOrLabels(Match):
    def __init__(self, namespaces_or_labels):
        self.namespaces_or_labels = namespaces_or_labels or []

    def match(self, other):
        log.debug('self.namespaces_or_labels: %s other.namespace: %s other.label: %s',
                  self.namespaces_or_labels, other.repository_spec.namespace, other.repository_spec.label)
        # TODO: should this matcher require a namespace string or a namespace object? either?
        return any([other.repository_spec.label in self.namespaces_or_labels,
                    other.repository_spec.namespace in self.namespaces_or_labels])
