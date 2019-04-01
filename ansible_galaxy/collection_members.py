import fnmatch
import logging
import os
import pprint

import attr

log = logging.getLogger(__name__)

# dirtools defaults to .git/.hg/.svn, but we need to extend that set
DEFAULT_IGNORE_DIRS = ['releases', 'CVS', '.bzr', '.hg', '.git', '.svn', '__pycache__',
                       '.tox']
DEFAULT_IGNORE_PATTERNS = ['*.pyc', '*.retry']

pf = pprint.pformat

# start with a ftw over collection_path, and refine from there


def file_is_excluded(filename, exclude_patterns):
    '''Check a filename against a list of exclude patterns'''
    return any([fnmatch.fnmatch(filename, pattern) for pattern in exclude_patterns])


@attr.s
class FileWalker(object):
    collection_path = attr.ib()
    file_errors = attr.ib(factory=list)
    ignore_dirs = attr.ib(default=DEFAULT_IGNORE_DIRS)
    exclude_patterns = attr.ib(default=DEFAULT_IGNORE_PATTERNS)

    def walk(self):
        full_collection_path = os.path.abspath(self.collection_path)

        yield full_collection_path

        for dirpath, dirnames, filenames in os.walk(full_collection_path,
                                                    onerror=self.on_walk_error,
                                                    followlinks=False):
            # filter out .git etc
            # NOTE: This modifies dirnames while it is being walked over
            for dirname in dirnames:
                if dirname in self.ignore_dirs:
                    dirnames.remove(dirname)
                else:
                    dir_full_path = os.path.join(dirpath, dirname)
                    yield dir_full_path

            for filename in filenames:

                full_path = os.path.join(dirpath, filename)

                if file_is_excluded(full_path, self.exclude_patterns):
                    continue

                yield full_path

    def on_walk_error(self, walk_error):
        log.warning('walk error on %s: %s', walk_error.filename, walk_error)
        self.file_errors.append(walk_error)


@attr.s
class CollectionMembers(object):
    walker = attr.ib(default=None)

    def walk(self):
        return self.walker.walk()

    # TODO: could/should make CollectionMembers iterable with a iter() ?
    def run(self):
        '''collect/walk, then filter found members, yield the members'''
        _members = self.walk()

        for _member in _members:
            yield _member
