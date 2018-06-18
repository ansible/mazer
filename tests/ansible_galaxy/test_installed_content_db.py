import logging
import os

from ansible_galaxy import installed_content_db

log = logging.getLogger(__name__)


def test_installed_content_db(galaxy_context):
    icd = installed_content_db.InstalledContentDatabase(galaxy_context)

    for x in icd.select():
        log.debug('x: %s', x)


def test_installed_content_db_match_names(galaxy_context):
    icd = installed_content_db.InstalledContentDatabase(galaxy_context)

    match_filter = installed_content_db.MatchNames(['foo.bar'])
    for x in icd.select(match_filter):
        log.debug('x: %s', x)


def test_installed_content_iterator(galaxy_context):
    ici = installed_content_db.installed_content_iterator(galaxy_context,
                                                          content_type='role')

    for i in ici:
        log.debug(i)


def test_installed_content_iterator_tmp_content(galaxy_context):
    ici = installed_content_db.installed_content_iterator(galaxy_context,
                                                          content_type='role')

    content_path = galaxy_context.content_path

    # make some 'namespace_paths' in temp content_path
    tmp_namespace_paths = ['ns1.repo1', 'ns1.repo2', 'ns2.repo1']
    content_type_dirs = ['roles']
    content_names = ['role1', 'role2', 'role3']
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
        log.debug(i)
