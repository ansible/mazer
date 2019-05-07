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


# FIXME: shouldn't need to patch object directly
import ansible_galaxy_cli

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

        archive_path = os.path.dirname(os.path.abspath(__file__))
        archive_path = os.path.join(archive_path, 'data', 'delete_me.tar.gz')
        tar = tarfile.open(archive_path, 'r:gz')
        tar.extractall(path=".")
        cls.role_dir = "./delete_me"
        cls.role_name = "unittest.delete_me"

        # add a meta/main.yml
        test_dir = os.path.join(cls.role_dir, 'meta')
        ensure_dir(test_dir)
        with open(os.path.join(cls.role_dir, 'meta/main.yml'), 'w') as fd:
            fd.write('galaxy_info: {}\ndependencies: {}')

        # making a temp dir for role installation
        cls.role_path = os.path.join(tempfile.mkdtemp(), "roles")

        ensure_dir(cls.role_path)

        # creating a tar file name for class data
        cls.role_tar = './delete_me.tar.gz'
        cls.makeTar(cls.role_tar, cls.role_dir)

    @classmethod
    def makeTar(cls, output_file, source_dir):
        ''' used for making a tarfile from a role directory '''
        # adding directory into a tar file
        try:
            tar = tarfile.open(output_file, "w:gz")
            tar.add(source_dir, arcname=os.path.basename(source_dir))
        except AttributeError:  # tarfile obj. has no attribute __exit__ prior to python 2.7
            pass
        finally:  # ensuring closure of tarfile obj
            tar.close()

    @classmethod
    def tearDownClass(cls):
        '''After tests are finished removes things created in setUpClass'''
        # deleting the temp role directory
        if os.path.exists(cls.role_dir):
            shutil.rmtree(cls.role_dir)
        if os.path.exists(cls.role_tar):
            os.remove(cls.role_tar)
        if os.path.isdir(cls.role_path):
            shutil.rmtree(cls.role_path)

    def setUp(self):
        # self.default_args = ['ansible-galaxy']
        # self.default_args = ['mazer', '--config', 'tests/configs/galaxy.yml']
        self.default_args = ['mazer']

    def test_run(self):
        ''' verifies that the GalaxyCLI object's api is created and that execute() is called. '''
        # gc = GalaxyCLI(args=self.default_args + ["install", "--ignore-errors", "imaginary_role"])
        gc = GalaxyCLI(args=["mazer", "install", "--ignore-errors", "imaginary_role"])
        gc.parse()
        with patch.object(ansible_galaxy_cli.cli.CLI, "execute", return_value=None) as mock_ex:
            with patch.object(ansible_galaxy_cli.cli.CLI, "run", return_value=None) as mock_run:
                gc.run()

                # testing
                self.assertEqual(mock_run.call_count, 1)
                self.assertEqual(mock_ex.call_count, 1)

    def test_execute_remove(self):
        # installing role
        log.debug('self.role_path: %s', self.role_path)

        gc = GalaxyCLI(args=self.default_args + ["install", "--collections-path", self.role_path, '--force', self.role_name])
        gc.parse()
        gc.run()

        log.debug('self.role_name: %s', self.role_name)
        # location where the role was installed
        role_file = os.path.join(self.role_path, self.role_name)

        # self.assertTrue(os.path.exists(role_file))
        log.debug('role_file: %s', role_file)

        # removing role
        # args = ["ansible-galaxy", "remove", role_file, self.role_name]
        args = self.default_args + ["remove", self.role_name]
        log.debug('args: %s', args)
        gc = GalaxyCLI(args=args)
        gc.parse()
        gc.run()

        # testing role was removed
        removed_role = not os.path.exists(role_file)
        self.assertTrue(removed_role)

    def test_raise_without_ignore_without_flag(self):
        ''' tests that GalaxyCLI exits with the error specified if the --ignore-errors flag is not used '''
        gc = GalaxyCLI(args=self.default_args + ["install", "--server=None", "testing.fake_role_name"])
        gc.parse()
        # testing that error expected is raised
        self.assertRaises(exceptions.GalaxyError, gc.run)
        # self.assertTrue(mocked_display.called_once_with("- downloading role 'fake_role_name', owned by "))

    def test_raise_without_ignore_with_flag(self):
        ''' tests that GalaxyCLI exits without the error specified if the --ignore-errors flag is used  '''
        # testing with --ignore-errors flag
        gc = GalaxyCLI(args=self.default_args + ["install", "--server=None", "testing.fake_role_name", "--ignore-errors"])
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
                'install': 'usage: %prog install [options] [-r FILE | repo_name(s)[,version] | scm+repo_url[,version] | tar_file(s)]',
                'list': 'usage: %prog list [repo_name]',
                'publish': 'usage: %prog publish [options] archive_path',
                'remove': 'usage: %prog remove repo1 repo2 ...',
                'version': 'usage: %prog version',
            }

            first_call = 'usage: %prog [build|info|install|list|migrate_role|publish|remove|version] [--help] [options] ...'
            second_call = formatted_call[action]
            calls = [call(first_call), call(second_call)]
            mocked_usage.assert_has_calls(calls)

    def test_parse_no_action(self):
        ''' testing the options parser when no action is given '''
        gc = GalaxyCLI(args=self.default_args + [""])
        self.assertRaises(cli_exceptions.CliOptionsError, gc.parse)

    def test_parse_invalid_action(self):
        ''' testing the options parser when an invalid action is given '''
        gc = GalaxyCLI(args=self.default_args + ["NOT_ACTION"])
        self.assertRaises(cli_exceptions.CliOptionsError, gc.parse)

    def test_parse_info(self):
        ''' testing the options parser when the action 'info' is given '''
        gc = GalaxyCLI(args=self.default_args + ["info"])
        self.run_parse_common(gc, "info")
        self.assertEqual(gc.options.offline, False)

    def test_parse_install(self):
        ''' testing the options parser when the action 'install' is given '''
        gc = GalaxyCLI(args=self.default_args + ["install"])
        self.run_parse_common(gc, "install")
        self.assertEqual(gc.options.ignore_errors, False)
        self.assertEqual(gc.options.no_deps, False)
        self.assertEqual(gc.options.force, False)

    def test_parse_list(self):
        ''' testing the options parser when the action 'list' is given '''
        gc = GalaxyCLI(args=self.default_args + ["list"])
        self.run_parse_common(gc, "list")
        self.assertEqual(gc.options.verbosity, 0)

    def test_parse_publish(self):
        ''' testing the options parser when the action 'publish' is given '''
        gc = GalaxyCLI(args=self.default_args + ["publish"])
        self.run_parse_common(gc, "publish")
        self.assertEqual(gc.options.verbosity, 0)

    def test_parse_remove(self):
        ''' testing the options parser when the action 'remove' is given '''
        gc = GalaxyCLI(args=self.default_args + ["remove"])
        self.run_parse_common(gc, "remove")
        self.assertEqual(gc.options.verbosity, 0)

    def test_parse_version(self):
        ''' testing the options parser when the action 'version' is given '''
        gc = GalaxyCLI(args=self.default_args + ["version"])
        self.run_parse_common(gc, "version")
        self.assertEqual(gc.options.verbosity, 0)
