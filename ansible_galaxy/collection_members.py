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
class CollectionMember(object):
    '''The info need to add a file to a archive (orig path, dest path, etc)'''
    src_full_path = attr.ib()
    dest_relative_path = attr.ib()


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
                    # log.debug('ignoring dir: %s', dirname)
                    dirnames.remove(dirname)
                else:
                    dir_full_path = os.path.join(dirpath, dirname)
                    # log.debug('yield dir_full_path: %s', dir_full_path)
                    yield dir_full_path

            for filename in filenames:
                # log.debug('fn dirpath: %s filename: %s', dirpath, filename)

                full_path = os.path.join(dirpath, filename)
                # log.debug('full_path: %s', full_path)

                # collection_relative_path = os.path.relpath(full_path, self.collection_path)

                # log.debug('collection_relative_path: %s', collection_relative_path)

                if file_is_excluded(full_path, self.exclude_patterns):
                    continue

                # log.debug('yield (fn full_path)%s', full_path)
                yield full_path
                # yield collection_relative_path
                # yield CollectionMember(src_full_path=full_path, dest_relative_path=collection_relative_path)

    def relative_walk(self):
        for full_path in self.walk():
            # rel_path = collection_member.dest_relative_path
            relative_path = os.path.relpath(full_path, self.collection_path)

            yield relative_path

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
