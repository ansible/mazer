import fnmatch
import logging
import os
import pprint

import attr

# not surprisingly, setuptools_scm needs very similar file finder utils
import setuptools_scm
import setuptools_scm.file_finder_git

log = logging.getLogger(__name__)

# dirtools defaults to .git/.hg/.svn, but we need to extend that set
DEFAULT_IGNORE_DIRS = ['CVS', '.bzr', '.hg', '.git', '.svn', 'releases', '__pycache__']
DEFAULT_IGNORE_PATTERNS = ['*.pyc', '*.retry']

pf = pprint.pformat

# start with a ftw over collection_path, and refine from there


@attr.s
class ScmFilesWalker(object):
    collection_path = attr.ib()

    def walk(self):
        '''recursively find members under collection_path and return a list'''
        # just the files from scm, though this will need to change if/when we support
        # binary modules or other 'compiled' content
        scm_files = setuptools_scm.file_finder_git.git_find_files(self.collection_path)

        for full_filename in scm_files:
            yield full_filename


@attr.s
class FileWalker(object):
    collection_path = attr.ib()
    file_errors = attr.ib(factory=list)
    ignore_dirs = attr.ib(default=DEFAULT_IGNORE_DIRS)
    exclude_patterns = attr.ib(default=DEFAULT_IGNORE_PATTERNS)

    def walk(self):
        for dirpath, dirnames, filenames in os.walk(self.collection_path,
                                                    onerror=self.on_walk_error,
                                                    followlinks=False):
            # filter out .git etc
            # NOTE: This modifies dirnames while it is being walked over
            for dirname in dirnames:
                if dirname in self.ignore_dirs:
                    dirnames.remove(dirname)

            for filename in filenames:
                full_path = os.path.join(dirpath, filename)
                if self.patterns_match(full_path, self.exclude_patterns):
                    continue

                yield full_path

    def relative_walk(self):
        for full_path in self.walk():
            rel_path = os.path.relpath(full_path, self.collection_path)

            yield rel_path

    def patterns_match(self, filename, patterns):
        for pattern in patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True
        return False

    def on_walk_error(self, walk_error):
        log.warning('walk error on %s: %s', walk_error.filename, walk_error)


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

            if self.post_filter(_member):
                yield _member
            else:
                log.debug('_member post filtered out: %s', _member)

    # TODO: track members that were filtered out?
    def post_filter(self, member):
        return True
