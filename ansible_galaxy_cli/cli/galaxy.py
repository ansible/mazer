########################################################################
#
# (C) 2013, James Cammarata <jcammarata@ansible.com>
#
# This file is part of Ansible
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
#
########################################################################

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import logging
import optparse
import os
import sys

from ansible_galaxy_cli import cli
from ansible_galaxy_cli import __version__ as galaxy_cli_version
from ansible_galaxy.actions import install
from ansible_galaxy.actions import info
from ansible_galaxy.actions import init
from ansible_galaxy.actions import list as list_action
from ansible_galaxy.actions import remove
from ansible_galaxy.actions import version
from ansible_galaxy.config import defaults
from ansible_galaxy.config import config
from ansible_galaxy_cli import exceptions as cli_exceptions
from ansible_galaxy import matchers
from ansible_galaxy.models.context import GalaxyContext

from ansible_galaxy import rest_api

# FIXME: not a model...
from ansible_galaxy.models.content import CONTENT_TYPES

log = logging.getLogger(__name__)


def exit_without_ignore(ignore_errors, msg=None, rc=1):
    """
    Exits with the specified return code unless the
    option --ignore-errors was specified
    """
    ignore_error_blurb = '- you can use --ignore-errors to skip failed roles and finish processing the list.'
    if not ignore_errors:
        message = ignore_error_blurb
        if msg:
            message = '%s:\n%s' % (msg, ignore_error_blurb)
        raise cli_exceptions.GalaxyCliError(message)


class GalaxyCLI(cli.CLI):
    '''command to manage Ansible roles in shared repostories, the default of which is Ansible Galaxy *https://galaxy.ansible.com*.'''

    SKIP_INFO_KEYS = ("name", "description", "readme_html", "related", "summary_fields", "average_aw_composite", "average_aw_score", "url")
    VALID_ACTIONS = ("info", "init", "install", "list", "remove", "version")
    VALID_ACTION_ALIASES = {'content-install': 'install'}

    def __init__(self, args):
        self.api = None
        super(GalaxyCLI, self).__init__(args)

    def set_action(self):

        super(GalaxyCLI, self).set_action()

        # specific to actions
        if self.action == "info":
            self.parser.set_usage("usage: %prog info [options] repo_name[,version]")

        elif self.action == "init":
            self.parser.set_usage("usage: %prog init [options] role_name")
            self.parser.add_option('--init-path', dest='init_path', default="./",
                                   help='The path in which the skeleton role will be created. The default is the current working directory.')
            self.parser.add_option('--type', dest='role_type', action='store', default='default',
                                   help="Initialize using an alternate role type. Valid types include: 'default' and 'apb'.")
            self.parser.add_option('--role-skeleton', dest='role_skeleton', default=None,
                                   help='The path to a role skeleton that the new role should be based upon.')

        elif self.action == "install":
            self.parser.set_usage("usage: %prog install [options] [-r FILE | repo_name(s)[,version] | scm+repo_url[,version] | tar_file(s)]")
            self.parser.add_option('-i', '--ignore-errors', dest='ignore_errors', action='store_true', default=False,
                                   help='Ignore errors and continue with the next specified repo.')
            self.parser.add_option('-n', '--no-deps', dest='no_deps', action='store_true', default=False, help='Don\'t download roles listed as dependencies')
            self.parser.add_option('-r', '--role-file', dest='role_file', help='A file containing a list of roles to be imported')
            self.parser.add_option('-t', '--type', dest='content_type', default="all",
                                   # help='A type of Galaxy Content to install: role, module, etc',
                                   help=optparse.SUPPRESS_HELP)
            self.parser.add_option('--namespace', dest='namespace', default=None,
                                   help='The namespace to use when installing content (required for installs from local scm repo or archives)')
        elif self.action == "remove":
            self.parser.set_usage("usage: %prog remove repo1 repo2 ...")
        elif self.action == "list":
            self.parser.set_usage("usage: %prog list [repo_name]")
        elif self.action == "version":
            self.parser.set_usage("usage: %prog version")

        # options that apply to more than one action
        if self.action in ['init', 'info']:
            self.parser.add_option('--offline', dest='offline', default=False, action='store_true', help="Don't query the galaxy API when creating roles")

        if self.action not in ("init", "version"):
            # NOTE: while the option type=str, the default is a list, and the
            # callback will set the value to a list.
            self.parser.add_option('-p', '--roles-path', dest='roles_path', action="append", default=[],
                                   help='The path to the directory containing your roles. The default is the roles_path configured in your ansible.cfg'
                                        'file (/etc/ansible/roles if not configured)', type='str')
            self.parser.add_option('-C', '--content-path', dest='content_path',
                                   help='The path to the directory containing your galaxy content. The default is the content_path configured in your'
                                        'ansible.cfg file (/etc/ansible/content if not configured)', type='str')
        if self.action in ("init", "install"):
            self.parser.add_option('-f', '--force', dest='force', action='store_true', default=False, help='Force overwriting an existing repo')

    def parse(self):
        ''' create an options parser for bin/ansible '''

        self.parser = cli.CLI.base_parser(
            usage="usage: %%prog [%s] [--help] [options] ..." % "|".join(self.VALID_ACTIONS),
            epilog="\nSee '%s <command> --help' for more information on a specific command.\n\n" % os.path.basename(sys.argv[0])
        )

        # common
        self.parser.add_option('-s', '--server', dest='server_url', default=None, help='The API server destination')

        self.parser.add_option('-c', '--ignore-certs', action='store_true', dest='ignore_certs', default=None,
                               help='Ignore SSL certificate validation errors.')
        self.set_action()

        super(GalaxyCLI, self).parse()

    def _get_galaxy_context(self, options, config):
        # use content_path from options if availble but fallback to configured content_path
        options_content_path = None
        if hasattr(options, 'content_path'):
            options_content_path = options.content_path

        raw_content_path = options_content_path or config.content_path

        content_path = os.path.expanduser(raw_content_path)

        # server is a dict like:
        # {'url': 'http://localhost',
        #  'ignore_certs': False}
        server = config.server.copy()

        if getattr(options, 'server_url', None):
            server['url'] = options.server_url

        if getattr(options, 'ignore_certs', None):
            # use ignore certs from options if available, but fallback to configured ignore_certs
            server['ignore_certs'] = options.ignore_certs

        galaxy_context = GalaxyContext(server=server, content_path=content_path)

        return galaxy_context

    def run(self):

        raw_config_file_path = os.environ.get('ANSIBLE_GALAXY_CONFIG', defaults.CONFIG_FILE)
        self.config_file_path = os.path.abspath(os.path.expanduser(raw_config_file_path))

        super(GalaxyCLI, self).run()

        self.config = config.load(self.config_file_path)

        log.debug('configuration: %s', json.dumps(self.config.as_dict(), indent=None))

        # cli --server value or the url field of the first server in config
        # TODO: pass list of server config objects to GalaxyContext and/or create a GalaxyContext later
        # server_url = self.options.server_url or self.config['servers'][0]['url']
        # ignore_certs = self.options.ignore_certs or self.config['servers'][0]['ignore_certs']

        galaxy_context = self._get_galaxy_context(self.options, self.config)

        log.debug('galaxy context: %s', galaxy_context)

        self.api = rest_api.GalaxyAPI(galaxy_context)

        log.debug('execute action: %s', self.action)
        log.debug('execute action with options: %s', self.options)
        log.debug('execute action with args: %s', self.args)

        self.execute()

############################
# execute actions
############################

    # TODO: most of this logic should be out of cli class
    def execute_init(self):
        """
        creates the skeleton framework of a role that complies with the galaxy metadata format.
        """

        init_path = self.options.init_path
        force = self.options.force
        role_skeleton_path = self.options.role_skeleton

        role_name = self.args.pop(0).strip() if self.args else None
        if not role_name:
            raise cli_exceptions.CliOptionsError("- no role name specified for init")

        role_path = os.path.join(init_path, role_name)
        if os.path.exists(role_path):
            if os.path.isfile(role_path):
                raise cli_exceptions.GalaxyCliError("- the path %s already exists, but is a file - aborting" % role_path)
            elif not force:
                raise cli_exceptions.GalaxyCliError("- the directory %s already exists."
                                                    "you can use --force to re-initialize this directory,\n"
                                                    "however it will reset any main.yml files that may have\n"
                                                    "been modified there already." % role_path)

        if role_skeleton_path is not None:
            skeleton_ignore_expressions = self.config.options['role_skeleton_ignore']
        else:
            this_dir, this_filename = os.path.split(__file__)

            type_path = getattr(self.options, 'role_type', "default")
            role_skeleton_path = os.path.join(this_dir, '../', 'data/role_skeleton', type_path)

            self.log.debug('role_skeleton_path: %s', role_skeleton_path)

            skeleton_ignore_expressions = ['^.*/.git_keep$']

        return init.init(role_name,
                         init_path,
                         role_path,
                         force,
                         role_skeleton_path,
                         skeleton_ignore_expressions,
                         self.options.role_type,
                         display_callback=self.display)

    def execute_info(self):
        """
        prints out detailed information about an installed role as well as info available from the galaxy API.
        """

        if len(self.args) == 0:
            # the user needs to specify a role
            raise cli_exceptions.CliOptionsError("- you must specify a user/role name")

        log.debug('args=%s', self.args)

        galaxy_context = self._get_galaxy_context(self.options, self.config)

        content_specs = self.args

        # FIXME: rc?
        return info.info_content_specs(galaxy_context, self.api, content_specs,
                                       display_callback=self.display,
                                       offline=self.options.offline)

    def execute_install(self):
        """
        uses the args list of roles to be installed, unless -f was specified. The list of roles
        can be a name (which will be downloaded via the galaxy API and github), or it can be a local .tar.gz file.
        """

        install_content_type = self.options.content_type

        # FIXME - still not sure where to put this or how best to handle it,
        #         but for now just detect when it's not provided and offer up
        #         default paths
        #
        # NOTE: kind of gaming the arg parsing here with self.options.content_path,
        #       and how CLI.unfrack_paths works. It's a bit of a hack... should
        #       probably find a better solution before this goes GA
        #
        # Fix content_path if this was not provided
        if self.options.content_type != "all" and self.options.content_type not in CONTENT_TYPES:
            raise cli_exceptions.CliOptionsError(
                "- invalid Galaxy Content type provided: %s\n  - Expected one of: %s" %
                (self.options.content_type, ", ".join(CONTENT_TYPES))
            )

        # TODO: mv to GalaxyContext constructor
        # If someone provides a --roles-path at the command line, we assume this is
        # for use with a legacy role and we want to maintain backwards compat
        if self.options.roles_path:
            self.log.warn('Assuming content is of type "role" since --role-path was used')
            install_content_type = 'role'

        self.log.debug('self.options: %s', self.options)
        galaxy_context = self._get_galaxy_context(self.options, self.config)

        # FIXME - add more types here, PoC is just role/module
        # TODO: more prep here?
        requested_content_specs = self.args

        try:
            rc = install.install_content_specs(galaxy_context,
                                               content_spec_strings=requested_content_specs,
                                               install_content_type=install_content_type,
                                               namespace_override=self.options.namespace,
                                               display_callback=self.display,
                                               ignore_errors=self.options.ignore_errors,
                                               no_deps=self.options.no_deps,
                                               force_overwrite=self.options.force)
        except Exception as e:
            log.exception(e)
            raise

        return rc

    def execute_remove(self):
        """
        removes the list of roles passed as arguments from the local system.
        """

        if len(self.args) == 0:
            raise cli_exceptions.CliOptionsError('- you must specify at least one role to remove.')

        galaxy_context = self._get_galaxy_context(self.options, self.config)

        if self.args:
            match_filter = matchers.MatchLabels(self.args)

        return remove.remove(galaxy_context,
                             repository_match_filter=match_filter,
                             display_callback=self.display)

    def execute_list(self):
        """
        lists the roles installed on the local system or matches a single role passed as an argument.
        """

        galaxy_context = self._get_galaxy_context(self.options, self.config)

        match_filter = matchers.MatchAll()

        if self.args:
            match_filter = matchers.MatchNamespacesOrLabels(self.args)

        return list_action.list(galaxy_context,
                                repository_match_filter=match_filter,
                                display_callback=self.display)

    def execute_version(self):
        return version.version(config_file_path=self.config_file_path,
                               cli_version=galaxy_cli_version,
                               display_callback=self.display)
