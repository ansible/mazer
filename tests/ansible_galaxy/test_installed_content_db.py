import logging
import os
import fnmatch

from ansible_galaxy import installed_content_db
from ansible_galaxy import matchers

log = logging.getLogger(__name__)


def test_installed_content_db(galaxy_context):
    icd = installed_content_db.InstalledContentDatabase(galaxy_context)

    for x in icd.select():
        log.debug('x: %s', x)


def test_installed_content_db_match_names(galaxy_context):
    icd = installed_content_db.InstalledContentDatabase(galaxy_context)

    match_filter = matchers.MatchNames(['foo.bar'])
    for x in icd.select(content_match_filter=match_filter):
        log.debug('x: %s', x)


def test_installed_content_iterator(galaxy_context):
    ici = installed_content_db.installed_content_iterator(galaxy_context,
                                                          content_type='role')

    for i in ici:
        log.debug(i)


class MatchContentNamesFnmatch(object):
    def __init__(self, fnmatch_patterns):
        self.fnmatch_patterns = fnmatch_patterns

    def __call__(self, other):
        return self.match(other)

    def match(self, other):
        # log.debug('self.fnmatch_patterns: %s other.name: %s', self.fnmatch_patterns, other.name)
        # log.debug('fnm: %s', fnmatch.fnmatch(other.name, self.fnmatch_patterns[0]))
        return any([fnmatch.fnmatch(other.name, x) for x in self.fnmatch_patterns])


def test_installed_content_iterator_empty(galaxy_context, mocker):
    mocker.patch('ansible_galaxy.installed_namespaces_db.get_namespace_paths',
                 return_value=iter(['foo', 'blip']))
    mocker.patch('ansible_galaxy.installed_repository_db.get_repository_paths',
                 return_value=iter(['bar', 'baz']))

    # The content type specific content iterator is determined at runtime, so we need to patch the value
    # of the 'roles' item in installed_repository_content_iterator_map to patch the right method used
    mocker.patch.dict('ansible_galaxy.installed_content_db.installed_repository_content_iterator_map',
                      {'roles': mocker.Mock(return_value=iter(['/dev/null/content/foo/bar/roles/role-1', '/dev/null/content/blip/baz/roles/role-2']))})

    ici = installed_content_db.installed_content_iterator(galaxy_context,
                                                          content_type='roles')
    log.debug('ici: %s', ici)

    installed_content = list(ici)
    log.debug('installed_content: %s', installed_content)
    assert installed_content[0]['content_data'].name == 'role-1'


def test_installed_content_iterator_tmp_content(galaxy_context):
    ici = installed_content_db.installed_content_iterator(galaxy_context,
                                                          content_type='roles')

    content_path = galaxy_context.content_path

    # make some 'namespace_paths' in temp content_path
    tmp_namespace_paths = ['ns1.repo1', 'ns1.repo2', 'ns2.repo1']
    content_type_dirs = ['roles']
    content_names = ['somerole1', 'somerole2', 'role3']
    role_subdirs = ['meta', 'tasks']

    # TODO/FIXME: replace file access/tmp stuff with mocking
    for tmp_namespace_path in tmp_namespace_paths:
        for content_type_dir in content_type_dirs:
            for content_name in content_names:
                for role_subdir in role_subdirs:
                    full_content_path = os.path.join(content_path, tmp_namespace_path, content_type_dir, content_name, role_subdir)
                    log.debug('full_content_path: %s', full_content_path)
                    os.makedirs(full_content_path)

                    main_yml = os.path.join(full_content_path, 'main.yml')
                    with open(main_yml, 'w') as fd:
                        fd.write('---\n')

                    if role_subdir == 'meta':
                        install_info = os.path.join(full_content_path, '.galaxy_install_info')
                        with open(install_info, 'w') as fd:
                            fd.write('version: 1.2.3\n')

    for i in ici:
        log.debug('ici stuff: %s', i)

    ici2 = installed_content_db.installed_content_iterator(galaxy_context,
                                                           content_match_filter=MatchContentNamesFnmatch(['somerole*', 'asdfsd']),
                                                           content_type='roles')

    for i in ici2:
        log.debug('i2: %s', i)
