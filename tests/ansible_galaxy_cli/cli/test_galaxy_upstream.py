# (c) 2016, Adrian Likins <alikins@redhat.com>
#
# This file is original part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

# import ansible
import errno
import os
import logging
import shutil
import tarfile
import tempfile

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import call, patch
import yaml


# FIXME: shouldn't need to patch object directly
import ansible_galaxy_cli
import ansible_galaxy

from ansible_galaxy import exceptions

from ansible_galaxy_cli.cli.galaxy import GalaxyCLI
from ansible_galaxy_cli import exceptions as cli_exceptions

log = logging.getLogger(__name__)


def ensure_dir(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            log.exception(e)
            raise


class TestGalaxy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        '''creating prerequisites for installing a role; setUpClass occurs ONCE whereas setUp occurs with every method tested.'''
        # class data for easy viewing: role_dir, role_tar, role_name, role_req, role_path

        if os.path.exists("./delete_me"):
            shutil.rmtree("./delete_me")

        # creating framework for a role
        gc = GalaxyCLI(args=["ansible-galaxy", "init", "--offline", "delete_me", "--type", "role"])
        gc.parse()
        gc.run()
        cls.role_dir = "./delete_me"
        cls.role_name = "unittest.delete_me"

        # add a meta/main.yml
        test_dir = os.path.join(cls.role_dir, 'meta')

        ensure_dir(test_dir)
        fd = open(os.path.join(cls.role_dir, 'meta/main.yml'), 'w')

        fd.write('galaxy_info: {}\ndependencies: {}')
        fd.close()
        # making a temp dir for role installation
        cls.role_path = os.path.join(tempfile.mkdtemp(), "roles")

        ensure_dir(cls.role_path)

        # creating a tar file name for class data
        cls.role_tar = './delete_me.tar.gz'
        cls.makeTar(cls.role_tar, cls.role_dir)

        # creating a temp file with installation requirements
        cls.role_req = './delete_me_requirements.yml'
        fd = open(cls.role_req, "w")

        dep_lines = ["- 'src': '%s'\n" % cls.role_tar,
                     "  'name': '%s'\n" % cls.role_name,
                     "  'path': '%s'\n" % cls.role_path]
        log.debug('dep_lines: %s', dep_lines)
        for dep_line in dep_lines:
            fd.write(dep_line)

        fd.close()

    @classmethod
    def makeTar(cls, output_file, source_dir):
        ''' used for making a tarfile from a role directory '''
        # adding directory into a tar file
        try:
            tar = tarfile.open(output_file, "w:gz")
            tar.add(source_dir, arcname=os.path.basename(source_dir))
        except AttributeError:  # tarfile obj. has no attribute __exit__ prior to python 2.    7
            pass
        finally:  # ensuring closure of tarfile obj
            tar.close()

    @classmethod
    def tearDownClass(cls):
        '''After tests are finished removes things created in setUpClass'''
        # deleting the temp role directory
        if os.path.exists(cls.role_dir):
            shutil.rmtree(cls.role_dir)
        if os.path.exists(cls.role_req):
            os.remove(cls.role_req)
        if os.path.exists(cls.role_tar):
            os.remove(cls.role_tar)
        if os.path.isdir(cls.role_path):
            shutil.rmtree(cls.role_path)

    def setUp(self):
        self.default_args = ['ansible-galaxy']

    def test_init(self):
        galaxy_cli = GalaxyCLI(args=self.default_args)
        self.assertTrue(isinstance(galaxy_cli, GalaxyCLI))

    def test_run(self):
        ''' verifies that the GalaxyCLI object's api is created and that execute() is called. '''
        gc = GalaxyCLI(args=["ansible-galaxy", "install", "--ignore-errors", "imaginary_role"])
        gc.parse()
        with patch.object(ansible_galaxy_cli.cli.CLI, "execute", return_value=None) as mock_ex:
            with patch.object(ansible_galaxy_cli.cli.CLI, "run", return_value=None) as mock_run:
                gc.run()

                # testing
                self.assertEqual(mock_run.call_count, 1)
                self.assertTrue(isinstance(gc.api, ansible_galaxy.rest_api.GalaxyAPI))
                self.assertEqual(mock_ex.call_count, 1)

    def test_execute_remove(self):
        # installing role
        log.debug('self.role_path: %s', self.role_path)
        log.debug('self.role_req: %s', self.role_req)

        gc = GalaxyCLI(args=["ansible-galaxy", "install", "--content-path", self.role_path, "-r", self.role_req, '--force'])
        gc.parse()
        gc.run()

        log.debug('self.role_name: %s', self.role_name)
        # location where the role was installed
        role_file = os.path.join(self.role_path, self.role_name)

        log.debug('role_file: %s', role_file)

        # removing role
        # args = ["ansible-galaxy", "remove", role_file, self.role_name]
        args = ["ansible-galaxy", "remove", self.role_name]
        log.debug('args: %s', args)
        gc = GalaxyCLI(args=args)
        gc.parse()
        gc.run()

        # testing role was removed
        removed_role = not os.path.exists(role_file)
        self.assertTrue(removed_role)

    def test_exit_without_ignore_without_flag(self):
        ''' tests that GalaxyCLI exits with the error specified if the --ignore-errors flag is not used '''
        gc = GalaxyCLI(args=["ansible-galaxy", "install", "--server=None", "testing.fake_role_name"])
        gc.parse()
        # testing that error expected is raised
        self.assertRaises(exceptions.GalaxyError, gc.run)
        # self.assertTrue(mocked_display.called_once_with("- downloading role 'fake_role_name', owned by "))

    def test_exit_without_ignore_with_flag(self):
        ''' tests that GalaxyCLI exits without the error specified if the --ignore-errors flag is used  '''
        # testing with --ignore-errors flag
        gc = GalaxyCLI(args=["ansible-galaxy", "install", "--server=None", "testing.fake_role_name", "--ignore-errors"])
        gc.parse()
        gc.run()
        #    self.assertTrue(mocked_display.called_once_with("- downloading role 'fake_role_name', owned by "))

    def run_parse_common(self, galaxycli_obj, action):
        with patch.object(ansible_galaxy_cli.cli.SortedOptParser, "set_usage") as mocked_usage:
            galaxycli_obj.parse()

            # checking that the common results of parse() for all possible actions have been created/called
            self.assertIsInstance(galaxycli_obj.parser, ansible_galaxy_cli.cli.SortedOptParser)
            # self.assertIsInstance(galaxycli_obj.galaxy, ansible_galaxy.models.context.GalaxyContext)
            formatted_call = {
                'info': 'usage: %prog info [options] repo_name[,version]',
                'init': 'usage: %prog init [options] collection name',
                'install': 'usage: %prog install [options] [-r FILE | repo_name(s)[,version] | scm+repo_url[,version] | tar_file(s)]',
                'list': 'usage: %prog list [repo_name]',
                'remove': 'usage: %prog remove repo1 repo2 ...',
                'version': 'usage: %prog version',
            }

            first_call = 'usage: %prog [build|info|init|install|list|remove|version] [--help] [options] ...'
            second_call = formatted_call[action]
            calls = [call(first_call), call(second_call)]
            mocked_usage.assert_has_calls(calls)

    def test_parse_no_action(self):
        ''' testing the options parser when no action is given '''
        gc = GalaxyCLI(args=["ansible-galaxy", ""])
        self.assertRaises(cli_exceptions.CliOptionsError, gc.parse)

    def test_parse_invalid_action(self):
        ''' testing the options parser when an invalid action is given '''
        gc = GalaxyCLI(args=["ansible-galaxy", "NOT_ACTION"])
        self.assertRaises(cli_exceptions.CliOptionsError, gc.parse)

    def test_parse_info(self):
        ''' testing the options parser when the action 'info' is given '''
        gc = GalaxyCLI(args=["ansible-galaxy", "info"])
        self.run_parse_common(gc, "info")
        self.assertEqual(gc.options.offline, False)

    def test_parse_init(self):
        ''' testing the options parser when the action 'init' is given '''
        gc = GalaxyCLI(args=["ansible-galaxy", "init"])
        self.run_parse_common(gc, "init")
        self.assertEqual(gc.options.offline, False)
        self.assertEqual(gc.options.force, False)

    def test_parse_install(self):
        ''' testing the options parser when the action 'install' is given '''
        gc = GalaxyCLI(args=["ansible-galaxy", "install"])
        self.run_parse_common(gc, "install")
        self.assertEqual(gc.options.ignore_errors, False)
        self.assertEqual(gc.options.no_deps, False)
        self.assertEqual(gc.options.role_file, None)
        self.assertEqual(gc.options.force, False)

    def test_parse_list(self):
        ''' testing the options parser when the action 'list' is given '''
        gc = GalaxyCLI(args=["ansible-galaxy", "list"])
        self.run_parse_common(gc, "list")
        self.assertEqual(gc.options.verbosity, 0)

    def test_parse_remove(self):
        ''' testing the options parser when the action 'remove' is given '''
        gc = GalaxyCLI(args=["ansible-galaxy", "remove"])
        self.run_parse_common(gc, "remove")
        self.assertEqual(gc.options.verbosity, 0)

    def test_parse_version(self):
        ''' testing the options parser when the action 'version' is given '''
        gc = GalaxyCLI(args=["ansible-galaxy", "version"])
        self.run_parse_common(gc, "version")
        self.assertEqual(gc.options.verbosity, 0)


class ValidRoleTests(object):

    expected_role_dirs = ('defaults', 'files', 'handlers', 'meta', 'tasks', 'templates', 'vars', 'tests')
    # FIXME: there is some oddness with class attributes and setUpClass methods modifying them. Something
    #        to sort out when these get updated to pytest

    @classmethod
    def setup_class(cls):
        log.debug('setup_class container')
        log.debug('cls.content_type: %s', cls.content_type)
        if not cls.content_type:
            cls.content_type = 'role'
        content_type_dir = cls.content_type
        this_dir, _ = os.path.split(__file__)
        _role_skeleton_path = os.path.join(this_dir, '../../../', 'ansible_galaxy_cli/data/', 'skeleton', content_type_dir)
        log.debug('normpath(_role_skeleton_path): %s', os.path.normpath(_role_skeleton_path))
        cls.setUpRole('delete_me_%s' % cls.content_type,
                      skeleton_path=_role_skeleton_path,
                      galaxy_args=['--type=%s' % cls.content_type,
                                   '--skeleton=%s' % _role_skeleton_path])

    @classmethod
    def setUpRole(cls, role_name, skeleton_path, galaxy_args=None):
        if galaxy_args is None:
            galaxy_args = []

        log.debug('skeleton_path arg: %s', skeleton_path)

        # TODO: mock out role_skeleton path instead of always testing
        #       with --role-skeleton path to avoid issues like
        #       https://github.com/ansible/galaxy-cli/issues/20
        cls.role_skeleton_path = skeleton_path
        if '--skeleton' not in galaxy_args:
            galaxy_args += ['--skeleton', skeleton_path]
            log.debug('role_skeleton_path: %s', cls.role_skeleton_path)

        # Make temp directory for testing
        cls.test_dir = tempfile.mkdtemp()
        ensure_dir(cls.test_dir)
        log.debug('test_dir: %s', cls.test_dir)

        cls.role_dir = os.path.join(cls.test_dir, role_name)
        cls.role_name = role_name
        log.debug('role_dir: %s', cls.role_dir)
        log.debug('role_name: %s', cls.role_name)

        # create role using default skeleton
        gc_args = ['ansible-galaxy', 'init', '-c', '--offline'] + galaxy_args + ['--path', cls.test_dir, cls.role_name]
        log.debug('gc_args: %s', gc_args)
        gc = GalaxyCLI(args=gc_args)
        gc.parse()
        gc.run()
        cls.gc = gc

        if skeleton_path is None:
            cls.role_skeleton_path = gc.galaxy.default_role_skeleton_path

    @classmethod
    def tearDownClass(cls):
        if not os.path.isdir(cls.test_dir):
            return
        log.debug('deleting %s', cls.test_dir)
        shutil.rmtree(cls.test_dir)

    def test_metadata(self):
        with open(os.path.join(self.role_dir, 'meta', 'main.yml'), 'r') as mf:
            metadata = yaml.safe_load(mf)
        self.assertIn('galaxy_info', metadata, msg='unable to find galaxy_info in metadata')
        self.assertIn('dependencies', metadata, msg='unable to find dependencies in metadata')

    def test_readme(self):
        readme_path = os.path.join(self.role_dir, 'README.md')
        self.assertTrue(os.path.exists(readme_path), msg='Readme doesn\'t exist')

    def test_main_ymls(self):
        need_main_ymls = set(self.expected_role_dirs) - set(['meta', 'tests', 'files', 'templates'])
        for d in need_main_ymls:
            main_yml = os.path.join(self.role_dir, d, 'main.yml')
            self.assertTrue(os.path.exists(main_yml), 'the main_yml path: %s does not exist' % main_yml)
            expected_string = "---\n# {0} file for {1}".format(d, self.role_name)
            log.debug('opening %s', main_yml)
            with open(main_yml, 'r') as f:
                self.assertEqual(expected_string, f.read().strip())

    def test_role_dirs(self):
        for d in self.expected_role_dirs:
            self.assertTrue(os.path.isdir(os.path.join(self.role_dir, d)), msg="Expected role subdirectory {0} doesn't exist".format(d))

    def test_travis_yml(self):
        with open(os.path.join(self.role_dir, '.travis.yml'), 'r') as f:
            contents = f.read()

        with open(os.path.join(self.role_skeleton_path, '.travis.yml'), 'r') as f:
            expected_contents = f.read()

        self.assertEqual(expected_contents, contents, msg='.travis.yml does not match expected')

    def test_test_yml(self):
        with open(os.path.join(self.role_dir, 'tests', 'test.yml'), 'r') as f:
            test_playbook = yaml.safe_load(f)
        self.assertEqual(len(test_playbook), 1)
        self.assertEqual(test_playbook[0]['hosts'], 'localhost')
        self.assertEqual(test_playbook[0]['remote_user'], 'root')
        self.assertListEqual(test_playbook[0]['roles'], [self.role_name], msg='The list of roles included in the test play doesn\'t match')


class TestGalaxyInitDefault(unittest.TestCase, ValidRoleTests):
    content_type = 'role'

    # @classmethod
    # def setup_class(cls):
    #    cls.setUpRole(role_name='delete_me', skeleton_path=cls._test_role_skeleton_path)

    def test_metadata_contents(self):
        with open(os.path.join(self.role_dir, 'meta', 'main.yml'), 'r') as mf:
            metadata = yaml.safe_load(mf)
        self.assertEqual(metadata.get('galaxy_info', dict()).get('author'), 'Your name', msg='author was not set properly in metadata')


class TestGalaxyInitAPB(unittest.TestCase, ValidRoleTests):
    content_type = 'apb'

    def test_metadata_apb_tag(self):
        meta_to_read = os.path.join(self.role_dir, 'meta', 'main.yml')
        log.debug('meta_to_read: %s', meta_to_read)
        with open(meta_to_read, 'r') as mf:
            metadata = yaml.safe_load(mf)
        self.assertIn('apb', metadata.get('galaxy_info', dict()).get('galaxy_tags', []), msg='apb tag not set in role metadata')

    def test_metadata_contents(self):
        with open(os.path.join(self.role_dir, 'meta', 'main.yml'), 'r') as mf:
            metadata = yaml.safe_load(mf)
        self.assertEqual(metadata.get('galaxy_info', dict()).get('author'), 'Your name', msg='author was not set properly in metadata')

    def test_apb_yml(self):
        self.assertTrue(os.path.exists(os.path.join(self.role_dir, 'apb.yml')), msg='apb.yml was not created')

    def test_test_yml(self):
        playbook_path_to_read = os.path.join(self.role_dir, 'tests', 'test.yml')
        log.debug('playbook_path_to_read: %s', playbook_path_to_read)
        with open(playbook_path_to_read, 'r') as f:
            test_playbook = yaml.safe_load(f)
        log.debug('test_playbook: %s', test_playbook)
        self.assertEqual(len(test_playbook), 1)
        self.assertEqual(test_playbook[0]['hosts'], 'localhost')
        self.assertEqual(test_playbook[0]['connection'], 'local')
        self.assertFalse(test_playbook[0]['gather_facts'])
        self.assertIsNone(test_playbook[0]['tasks'], msg='We\'re expecting an unset list of tasks in test.yml')


class TestGalaxyInitSkeleton(unittest.TestCase, ValidRoleTests):
    content_type = 'role'

    @classmethod
    def setup_class(cls):
        _test_role_skeleton_path = os.path.join(os.path.split(__file__)[0], 'data/role_skeleton')
        log.debug('_test_role_sp: %s', _test_role_skeleton_path)
        log.debug('normpath(_test_role_skeleton_path): %s', os.path.normpath(_test_role_skeleton_path))
        cls.setUpRole('delete_me_skeleton', skeleton_path=_test_role_skeleton_path)

    def test_empty_files_dir(self):
        files_dir = os.path.join(self.role_dir, 'files')
        self.assertTrue(os.path.isdir(files_dir))
        self.assertListEqual(os.listdir(files_dir), [], msg='we expect the files directory to be empty, is ignore working?')

    def test_template_ignore_jinja(self):
        test_conf_j2 = os.path.join(self.role_dir, 'templates', 'test.conf.j2')
        self.assertTrue(os.path.exists(test_conf_j2), msg="The test.conf.j2 template doesn't seem to exist, is it being rendered as test.conf?")
        with open(test_conf_j2, 'r') as f:
            contents = f.read()
        expected_contents = '[defaults]\ntest_key = {{ test_variable }}'
        self.assertEqual(expected_contents, contents.strip(), msg="test.conf.j2 doesn't contain what it should, is it being rendered?")

    def test_template_ignore_jinja_subfolder(self):
        test_conf_j2 = os.path.join(self.role_dir, 'templates', 'subfolder', 'test.conf.j2')
        self.assertTrue(os.path.exists(test_conf_j2), msg="The test.conf.j2 template doesn't seem to exist, is it being rendered as test.conf?")
        with open(test_conf_j2, 'r') as f:
            contents = f.read()
        expected_contents = '[defaults]\ntest_key = {{ test_variable }}'
        self.assertEqual(expected_contents, contents.strip(), msg="test.conf.j2 doesn't contain what it should, is it being rendered?")

    def test_template_ignore_similar_folder(self):
        self.assertTrue(os.path.exists(os.path.join(self.role_dir, 'templates_extra', 'templates.txt')))

    def test_skeleton_option(self):
        self.assertEquals(self.role_skeleton_path, self.gc.options.skeleton, msg='Skeleton path was not parsed properly from the command line')
