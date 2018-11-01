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


class MatchRepositorySpec(Match):
    def __init__(self, repository_specs):
        self.repository_specs = repository_specs or []

    def match(self, other):
        res = other.repository_spec in self.repository_specs
        log.debug('%s: is %s in %s', res, other.repository_spec, self.repository_specs)
        return res


class MatchRepositorySpecNamespaceName(Match):
    def __init__(self, repository_specs):
        self.namespaces_names = [(x.namespace, x.name) for x in repository_specs] or []

    def match(self, other):
        ns_n_match_res = False
        other_ns_n = (other.repository_spec.namespace, other.repository_spec.name)
        ns_n_match_res = other_ns_n in self.namespaces_names

        log.debug('%s (ns_n): does %s match %s?',
                  ns_n_match_res,
                  other_ns_n,
                  self.namespaces_names)

        return ns_n_match_res


class MatchRepositorySpecNamespaceNameVersion(Match):
    def __init__(self, repository_specs):
        self.namespaces_names_versions = [(x.namespace, x.name, x.version) for x in repository_specs] or []
        self.namespaces_names = [(x.namespace, x.name) for x in repository_specs] or []

    def match(self, other):
        ns_n_v_match_res = False

        other_ns_n_v = (other.repository_spec.namespace, other.repository_spec.name, other.repository_spec.version)

        ns_n_v_match_res = other_ns_n_v in self.namespaces_names_versions

        log.debug('%s (ns_n_v) : does %s match %s ?',
                  ns_n_v_match_res,
                  other_ns_n_v,
                  self.namespaces_names_versions)

        return ns_n_v_match_res


class MatchNamespace(Match):
    def __init__(self, namespaces_to_match):
        self.namespaces_to_match = namespaces_to_match or []
        self.log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))

    def match(self, other):
        res = other.namespace in self.namespaces_to_match
        self.log.debug('%s: (ns) %s matches %s', res, other.namespace, self.namespaces_to_match)
        return res


class MatchNamespacesOrLabels(Match):
    def __init__(self, namespaces_or_labels):
        self.namespaces_or_labels = namespaces_or_labels or []

    def match(self, other):
        log.debug('self.namespaces_or_labels: %s other.namespace: %s other.label: %s',
                  self.namespaces_or_labels, other.repository_spec.namespace, other.repository_spec.label)
        # TODO: should this matcher require a namespace string or a namespace object? either?
        return any([other.repository_spec.label in self.namespaces_or_labels,
                    other.repository_spec.namespace in self.namespaces_or_labels])
