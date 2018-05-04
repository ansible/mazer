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

import logging
import os.path
import re
import shutil
import sys
import time
import yaml

from jinja2 import Environment, FileSystemLoader

from ansible_galaxy_cli import cli
from ansible_galaxy.config import defaults
from ansible_galaxy.config import runtime
from ansible_galaxy import exceptions
from ansible_galaxy_cli import exceptions as cli_exceptions
from ansible_galaxy.models.context import GalaxyContext
from ansible_galaxy.utils.text import to_text

# FIXME: importing class, fix name collision later or use this style
# TODO: replace flat_rest_api with a OO interface
from ansible_galaxy.flat_rest_api.api import GalaxyAPI
from ansible_galaxy.flat_rest_api.login import GalaxyLogin
from ansible_galaxy.flat_rest_api.content import GalaxyContent
from ansible_galaxy.flat_rest_api.token import GalaxyToken

# FIXME: not a model...
from ansible_galaxy.models.content import CONTENT_TYPES

log = logging.getLogger(__name__)


class GalaxyCLI(cli.CLI):
    '''command to manage Ansible roles in shared repostories, the default of which is Ansible Galaxy *https://galaxy.ansible.com*.'''

    SKIP_INFO_KEYS = ("name", "description", "readme_html", "related", "summary_fields", "average_aw_composite", "average_aw_score", "url")
    VALID_ACTIONS = ("delete", "import", "info", "init", "install", "content-install", "list", "login", "remove", "search", "setup")

    def __init__(self, args):
        self.api = None
        self.galaxy = None
        super(GalaxyCLI, self).__init__(args)

    def set_action(self):

        super(GalaxyCLI, self).set_action()

        # specific to actions
        if self.action == "delete":
            self.parser.set_usage("usage: %prog delete [options] github_user github_repo")
        elif self.action == "import":
            self.parser.set_usage("usage: %prog import [options] github_user github_repo")
            self.parser.add_option('--no-wait', dest='wait', action='store_false', default=True, help='Don\'t wait for import results.')
            self.parser.add_option('--branch', dest='reference',
                                   help='The name of a branch to import. Defaults to the repository\'s default branch (usually master)')
            self.parser.add_option('--role-name', dest='role_name', help='The name the role should have, if different than the repo name')
            self.parser.add_option('--status', dest='check_status', action='store_true', default=False,
                                   help='Check the status of the most recent import request for given github_user/github_repo.')
        elif self.action == "info":
            self.parser.set_usage("usage: %prog info [options] role_name[,version]")
        elif self.action == "init":
            self.parser.set_usage("usage: %prog init [options] role_name")
            self.parser.add_option('--init-path', dest='init_path', default="./",
                                   help='The path in which the skeleton role will be created. The default is the current working directory.')
            self.parser.add_option('--type', dest='role_type', action='store', default='default',
                                   help="Initialize using an alternate role type. Valid types include: 'container', 'apb' and 'network'.")
            self.parser.add_option('--role-skeleton', dest='role_skeleton', default=runtime.GALAXY_ROLE_SKELETON,
                                   help='The path to a role skeleton that the new role should be based upon.')
        elif self.action == "install":
            self.parser.set_usage("usage: %prog install [options] [-r FILE | role_name(s)[,version] | scm+role_repo_url[,version] | tar_file(s)]")
            self.parser.add_option('-i', '--ignore-errors', dest='ignore_errors', action='store_true', default=False,
                                   help='Ignore errors and continue with the next specified role.')
            self.parser.add_option('-n', '--no-deps', dest='no_deps', action='store_true', default=False, help='Don\'t download roles listed as dependencies')
            self.parser.add_option('-r', '--role-file', dest='role_file', help='A file containing a list of roles to be imported')
            self.parser.add_option('-g', '--keep-scm-meta', dest='keep_scm_meta', action='store_true',
                                   default=False, help='Use tar instead of the scm archive option when packaging the role')
        elif self.action == "content-install":
            self.parser.set_usage("usage: %prog content-install [options] [-r FILE | role_name(s)[,version] | scm+role_repo_url[,version] | tar_file(s)]")
            self.parser.add_option('-i', '--ignore-errors', dest='ignore_errors', action='store_true', default=False,
                                   help='Ignore errors and continue with the next specified role.')
            self.parser.add_option('-n', '--no-deps', dest='no_deps', action='store_true', default=False, help='Don\'t download roles listed as dependencies')
            # FIXME - Unsure about keeping this around
            self.parser.add_option('-r', '--role-file', dest='role_file',
                                   help='A file containing a list of roles to be imported')
            self.parser.add_option('-t', '--type', dest='content_type', default="all", help='A type of Galaxy Content to install: role, module, etc')
        elif self.action == "remove":
            self.parser.set_usage("usage: %prog remove role1 role2 ...")
        elif self.action == "list":
            self.parser.set_usage("usage: %prog list [role_name]")
        elif self.action == "login":
            self.parser.set_usage("usage: %prog login [options]")
            self.parser.add_option('--github-token', dest='token', default=None, help='Identify with github token rather than username and password.')
        elif self.action == "search":
            self.parser.set_usage("usage: %prog search [searchterm1 searchterm2] [--galaxy-tags galaxy_tag1,galaxy_tag2] [--platforms platform1,platform2] "
                                  "[--author username]")
            self.parser.add_option('--platforms', dest='platforms', help='list of OS platforms to filter by')
            self.parser.add_option('--galaxy-tags', dest='galaxy_tags', help='list of galaxy tags to filter by')
            self.parser.add_option('--author', dest='author', help='GitHub username')
        elif self.action == "setup":
            self.parser.set_usage("usage: %prog setup [options] source github_user github_repo secret")
            self.parser.add_option('--remove', dest='remove_id', default=None,
                                   help='Remove the integration matching the provided ID value. Use --list to see ID values.')
            self.parser.add_option('--list', dest="setup_list", action='store_true', default=False, help='List all of your integrations.')

        # options that apply to more than one action
        if self.action in ['init', 'info']:
            self.parser.add_option('--offline', dest='offline', default=False, action='store_true', help="Don't query the galaxy API when creating roles")

        if self.action not in ("delete", "import", "init", "login", "setup"):
            # NOTE: while the option type=str, the default is a list, and the
            # callback will set the value to a list.
            self.parser.add_option('-p', '--roles-path', dest='roles_path', action="append", default=[],
                                   help='The path to the directory containing your roles. The default is the roles_path configured in your ansible.cfg'
                                        'file (/etc/ansible/roles if not configured)', type='str')
        if self.action in ("init", "install", "content-install"):
            self.parser.add_option('-f', '--force', dest='force', action='store_true', default=False, help='Force overwriting an existing role')

    def parse(self):
        ''' create an options parser for bin/ansible '''

        self.parser = cli.CLI.base_parser(
            usage="usage: %%prog [%s] [--help] [options] ..." % "|".join(self.VALID_ACTIONS),
            epilog="\nSee '%s <command> --help' for more information on a specific command.\n\n" % os.path.basename(sys.argv[0])
        )

        # common
        self.parser.add_option('-s', '--server', dest='api_server', default=runtime.GALAXY_SERVER, help='The API server destination')
        self.parser.add_option('-c', '--ignore-certs', action='store_true', dest='ignore_certs', default=runtime.GALAXY_IGNORE_CERTS,
                               help='Ignore SSL certificate validation errors.')
        self.set_action()

        super(GalaxyCLI, self).parse()

        # self.galaxy = base.Galaxy(self.options)
        self.galaxy = GalaxyContext(self.options)

    def run(self):

        super(GalaxyCLI, self).run()

        self.api = GalaxyAPI(self.galaxy)
        self.execute()

    def exit_without_ignore(self, rc=1):
        """
        Exits with the specified return code unless the
        option --ignore-errors was specified
        """
        if not self.options.ignore_errors:
            raise cli_exceptions.GalaxyCliError('- you can use --ignore-errors to skip failed roles and finish processing the list.')

    # TODO: move to a repr for Role?
    def _display_role_info(self, role_info):

        text = [u"", u"Role: %s" % to_text(role_info['name'])]
        text.append(u"\tdescription: %s" % role_info.get('description', ''))

        for k in sorted(role_info.keys()):

            if k in self.SKIP_INFO_KEYS:
                continue

            if isinstance(role_info[k], dict):
                text.append(u"\t%s:" % (k))
                for key in sorted(role_info[k].keys()):
                    if key in self.SKIP_INFO_KEYS:
                        continue
                    text.append(u"\t\t%s: %s" % (key, role_info[k][key]))
            else:
                text.append(u"\t%s: %s" % (k, role_info[k]))

        return u'\n'.join(text)

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

        # FIXME(akl): role_skeleton stuff should probably be a module or two and a few classes instead of inline here
        # role_skeleton ends mostly being a list of file paths to copy
        inject_data = dict(
            role_name=role_name,
            author='your name',
            description='your description',
            company='your company (optional)',
            license='license (GPLv2, CC-BY, etc)',
            issue_tracker_url='http://example.com/issue/tracker',
            min_ansible_version='1.2',
            role_type=self.options.role_type
        )

        import pprint
        self.log.debug('inject_data: %s', pprint.pformat(inject_data))

        # create role directory
        if not os.path.exists(role_path):
            os.makedirs(role_path)

        if role_skeleton_path is not None:
            skeleton_ignore_expressions = runtime.GALAXY_ROLE_SKELETON_IGNORE
        else:
            this_dir, this_filename = os.path.split(__file__)

            type_path = getattr(self.options, 'role_type', "default")
            role_skeleton_path = os.path.join(this_dir, '../', 'data/role_skeleton', type_path)

            self.log.debug('role_skeleton_path: %s', role_skeleton_path)

            skeleton_ignore_expressions = ['^.*/.git_keep$']

        role_skeleton = os.path.expanduser(role_skeleton_path)

        self.log.debug('role_skeleton: %s', role_skeleton)
        skeleton_ignore_re = [re.compile(x) for x in skeleton_ignore_expressions]

        template_env = Environment(loader=FileSystemLoader(role_skeleton))

        # TODO: mv elsewhere, this is main role install logic
        for root, dirs, files in os.walk(role_skeleton, topdown=True):
            rel_root = os.path.relpath(root, role_skeleton)
            in_templates_dir = rel_root.split(os.sep, 1)[0] == 'templates'
            dirs[:] = [d for d in dirs if not any(r.match(d) for r in skeleton_ignore_re)]

            for f in files:
                filename, ext = os.path.splitext(f)
                if any(r.match(os.path.join(rel_root, f)) for r in skeleton_ignore_re):
                    continue
                elif ext == ".j2" and not in_templates_dir:
                    src_template = os.path.join(rel_root, f)
                    dest_file = os.path.join(role_path, rel_root, filename)
                    template_env.get_template(src_template).stream(inject_data).dump(dest_file)
                else:
                    f_rel_path = os.path.relpath(os.path.join(root, f), role_skeleton)
                    shutil.copyfile(os.path.join(root, f), os.path.join(role_path, f_rel_path))

            for d in dirs:
                dir_path = os.path.join(role_path, rel_root, d)
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path)

        self.display("- %s was created successfully" % role_name)

    def execute_info(self):
        """
        prints out detailed information about an installed role as well as info available from the galaxy API.
        """

        if len(self.args) == 0:
            # the user needs to specify a role
            raise cli_exceptions.CliOptionsError("- you must specify a user/role name")

        roles_path = self.options.roles_path

        data = ''
        for role in self.args:

            role_info = {'path': roles_path}
            gr = GalaxyContent(self.galaxy, role)

            install_info = gr.install_info
            if install_info:
                if 'version' in install_info:
                    install_info['intalled_version'] = install_info['version']
                    del install_info['version']
                role_info.update(install_info)

            remote_data = False
            if not self.options.offline:
                remote_data = self.api.lookup_role_by_name(role, False)

            if remote_data:
                role_info.update(remote_data)

            if gr.metadata:
                role_info.update(gr.metadata)

            role_spec = GalaxyContent.yaml_parse({'role': role})
            if role_spec:
                role_info.update(role_spec)

            data = self._display_role_info(role_info)
            # FIXME: This is broken in both 1.9 and 2.0 as
            # _display_role_info() always returns something
            if not data:
                data = u"\n- the role %s was not found" % role

        self.display(data)

    def execute_content_install(self):
        """
        uses the args list of roles to be installed, unless -f was specified. The list of roles
        can be a name (which will be downloaded via the galaxy API and github), or it can be a local .tar.gz file.
        """

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

        self.log.debug('galaxy.options: %s', self.galaxy.options)
        # If someone provides a --roles-path at the command line, we assume this is
        # for use with a legacy role and we want to maintain backwards compat
        if self.options.roles_path:
            self.log.warn('Assuming content is of type "role" since --role-path was used')
            self.galaxy.content_paths = self.options.roles_path
            # self.galaxy.options['content_type'] = 'role'
            self.galaxy.options.content_type = 'role'

            # FIXME - add more types here, PoC is just role/module

        if len(self.args) == 0 and self.galaxy_file is None:
            # the user needs to specify one of either --role-file or specify a single user/role name
            raise cli_exceptions.CliOptionsError("- you must specify user/content name or a ansible-galaxy.yml file")

        no_deps = self.options.no_deps
        force = self.options.force

        content_left = []

        # FIXME - Need to handle role files here for backwards compat

        # roles were specified directly, so we'll just go out grab them
        # (and their dependencies, unless the user doesn't want us to).
        for content in self.args:
            galaxy_content = GalaxyContent.yaml_parse(content.strip())
            galaxy_content["type"] = self.options.content_type
            self.log.debug('content install galaxy_content: %s', galaxy_content)
            content_left.append(GalaxyContent(self.galaxy, **galaxy_content))

        for content in content_left:
            # only process roles in roles files when names matches if given

            # FIXME - not sure how to handle this scenario for ansible galaxy files
            #         here or if we even want to handle that scenario because of
            #         the galaxy content allowing blank repos to be inspected
            #
            #         maybe we want this but only for role types for backwards
            #         compat
            #
            # if role_file and self.args and role.name not in self.args:
            #    display.vvv('Skipping role %s' % role.name)
            #    continue

            log.debug('Processing %s %s ', content.content_type, content.name)

            # FIXME - Unsure if we want to handle the install info for all galaxy
            #         content. Skipping for non-role types for now.
            if content.content_type == "role":
                if content.install_info is not None:
                    if content.install_info['version'] != content.version or force:
                        if force:
                            self.display('- changing role %s from %s to %s' %
                                         (content.name, content.install_info['version'], content.version or "unspecified"))
                            content.remove()
                        else:
                            log.warn('- %s (%s) is already installed - use --force to change version to %s',
                                     content.name, content.install_info['version'], content.version or "unspecified")
                            continue
                    else:
                        if not force:
                            self.display('- %s is already installed, skipping.' % str(content))
                            continue

            try:
                installed = content.install()
            except cli_exceptions.GalaxyCliError as e:
                log.warning("- %s was NOT installed successfully: %s ", content.name, str(e))
                self.exit_without_ignore()
                continue

            # install dependencies, if we want them
            # FIXME - Galaxy Content Types handle dependencies in the GalaxyContent type itself because
            #         a content repo can contain many types and many of any single type and it's just
            #         easier to have that introspection there. In the future this should be more
            #         unified and have a clean API
            if content.content_type == "role":
                if not no_deps and installed:
                    if not content.metadata:
                        log.warning("Meta file %s is empty. Skipping dependencies.", content.path)
                    else:
                        role_dependencies = content.metadata.get('dependencies') or []
                        for dep in role_dependencies:
                            log.debug('Installing dep %s', dep)
                            dep_info = GalaxyContent.yaml_parse(dep)
                            dep_role = GalaxyContent(self.galaxy, **dep_info)
                            if '.' not in dep_role.name and '.' not in dep_role.src and dep_role.scm is None:
                                # we know we can skip this, as it's not going to
                                # be found on galaxy.ansible.com
                                continue
                            if dep_role.install_info is None:
                                if dep_role not in content_left:
                                    self.display('- adding dependency: %s' % str(dep_role))
                                    content_left.append(dep_role)
                                else:
                                    self.display('- dependency %s already pending installation.' % dep_role.name)
                            else:
                                if dep_role.install_info['version'] != dep_role.version:
                                    log.warning('- dependency %s from role %s differs from already installed version (%s), skipping',
                                                str(dep_role), content.name, dep_role.install_info['version'])
                                else:
                                    self.display('- dependency %s is already installed, skipping.' % dep_role.name)

            if not installed:
                log.warning("- %s was NOT installed successfully.", content.name)
                self.exit_without_ignore()

        return 0

    def execute_install(self):
        """
        uses the args list of roles to be installed, unless -f was specified. The list of roles
        can be a name (which will be downloaded via the galaxy API and github), or it can be a local .tar.gz file.
        """
        role_file = self.options.role_file

        if len(self.args) == 0 and role_file is None:
            # the user needs to specify one of either --role-file or specify a single user/role name
            raise cli_exceptions.CliOptionsError("- you must specify a user/role name or a roles file")

        no_deps = self.options.no_deps
        force = self.options.force

        roles_left = []
        if role_file:
            try:
                f = open(role_file, 'r')
                if role_file.endswith('.yaml') or role_file.endswith('.yml'):
                    try:
                        required_roles = yaml.safe_load(f.read())
                    except Exception as e:
                        raise cli_exceptions.GalaxyCliError("Unable to load data from the requirements file: %s" % role_file)

                    if required_roles is None:
                        raise cli_exceptions.GalaxyCliError("No roles found in file: %s" % role_file)

                    for role in required_roles:
                        if "include" not in role:
                            role = GalaxyContent.yaml_parse(role)
                            log.info("found role %s in yaml file", str(role))
                            if "name" not in role and "scm" not in role:
                                raise cli_exceptions.GalaxyCliError("Must specify name or src for role")
                            roles_left.append(GalaxyContent(self.galaxy, **role))
                        else:
                            with open(role["include"]) as f_include:
                                try:
                                    roles_left += [
                                        GalaxyContent(self.galaxy, **r) for r in
                                        (GalaxyContent.yaml_parse(i) for i in yaml.safe_load(f_include))
                                    ]
                                except Exception as e:
                                    msg = "Unable to load data from the include requirements file: %s %s"
                                    raise cli_exceptions.GalaxyCliError(msg % (role_file, e))
                else:
                    log.warn("DEPRECATED going forward only the yaml format will be supported (version='%s')", "2.6")
                    # roles listed in a file, one per line
                    for rline in f.readlines():
                        if rline.startswith("#") or rline.strip() == '':
                            continue
                        log.debug('found role %s in text file', str(rline))
                        role = GalaxyContent.yaml_parse(rline.strip())
                        roles_left.append(GalaxyContent(self.galaxy, **role))
                f.close()
            except (IOError, OSError) as e:
                raise cli_exceptions.GalaxyCliError('Unable to open %s: %s' % (role_file, str(e)))
        else:
            # roles were specified directly, so we'll just go out grab them
            # (and their dependencies, unless the user doesn't want us to).
            for rname in self.args:
                role = GalaxyContent.yaml_parse(rname.strip())
                roles_left.append(GalaxyContent(self.galaxy, **role))

        for role in roles_left:
            # only process roles in roles files when names matches if given
            if role_file and self.args and role.name not in self.args:
                log.info('Skipping role %s', role.name)
                continue

            log.info('Processing role %s ', role.name)

            # query the galaxy API for the role data

            if role.install_info is not None:
                if role.install_info['version'] != role.version or force:
                    if force:
                        self.display('- changing role %s from %s to %s' %
                                     role.name, role.install_info['version'], role.version or "unspecified")
                        role.remove()
                    else:
                        log.warn('- %s (%s) is already installed - use --force to change version to %s',
                                 role.name, role.install_info['version'], role.version or "unspecified")
                        continue
                else:
                    if not force:
                        self.display('- %s is already installed, skipping.' % str(role))
                        continue

            try:
                installed = role.install()
            except exceptions.GalaxyError as e:
                self.log.exception(e)
                log.warn("- %s was NOT installed successfully: %s ", role.name, str(e))
                self.exit_without_ignore()
                continue

            # install dependencies, if we want them
            if not no_deps and installed:
                if not role.metadata:
                    log.warn("Meta file %s is empty. Skipping dependencies.", role.path)
                else:
                    role_dependencies = role.metadata.get('dependencies') or []
                    for dep in role_dependencies:
                        log.debug('Installing dep %s', dep)
                        dep_info = GalaxyContent.yaml_parse(dep)
                        dep_role = GalaxyContent(self.galaxy, **dep_info)
                        if '.' not in dep_role.name and '.' not in dep_role.src and dep_role.scm is None:
                            # we know we can skip this, as it's not going to
                            # be found on galaxy.ansible.com
                            continue
                        if dep_role.install_info is None:
                            if dep_role not in roles_left:
                                self.display('- adding dependency: %s' % str(dep_role))
                                roles_left.append(dep_role)
                            else:
                                self.display('- dependency %s already pending installation.' % dep_role.name)
                        else:
                            if dep_role.install_info['version'] != dep_role.version:
                                log.warning('- dependency %s from role %s differs from already installed version (%s), skipping' %
                                            str(dep_role), role.name, dep_role.install_info['version'])
                            else:
                                self.display('- dependency %s is already installed, skipping.' % dep_role.name)

            if not installed:
                log.warning("- %s was NOT installed successfully.", role.name)
                self.exit_without_ignore()

        return 0

    def execute_remove(self):
        """
        removes the list of roles passed as arguments from the local system.
        """

        if len(self.args) == 0:
            raise cli_exceptions.CliOptionsError('- you must specify at least one role to remove.')

        for role_name in self.args:
            role = GalaxyContent(self.galaxy, role_name)
            try:
                if role.remove():
                    self.display('- successfully removed %s' % role_name)
                else:
                    self.display('- %s is not installed, skipping.' % role_name)
            except Exception as e:
                raise cli_exceptions.GalaxyCliError("Failed to remove role %s: %s" % (role_name, str(e)))

        return 0

    def execute_list(self):
        """
        lists the roles installed on the local system or matches a single role passed as an argument.
        """

        if len(self.args) > 1:
            raise cli_exceptions.CliOptionsError("- please specify only one role to list, or specify no roles to see a full list")

        if len(self.args) == 1:
            # show only the request role, if it exists
            name = self.args.pop()
            gr = GalaxyContent(self.galaxy, name)
            if gr.metadata:
                install_info = gr.install_info
                version = None
                if install_info:
                    version = install_info.get("version", None)
                if not version:
                    version = "(unknown version)"
                # show some more info about single roles here
                self.display("- %s, %s" % (name, version))
            else:
                self.display("- the role %s was not found" % name)
        else:
            # show all valid roles in the roles_path directory
            roles_path = self.options.roles_path
            for path in roles_path:
                role_path = os.path.expanduser(path)
                if not os.path.exists(role_path):
                    raise cli_exceptions.CliOptionsError("- the path %s does not exist. Please specify a valid path with --roles-path" % role_path)
                elif not os.path.isdir(role_path):
                    raise cli_exceptions.CliOptionsError("- %s exists, but it is not a directory. Please specify a valid path with --roles-path" % role_path)
                path_files = os.listdir(role_path)
                for path_file in path_files:
                    gr = GalaxyContent(self.galaxy, path_file)
                    if gr.metadata:
                        install_info = gr.install_info
                        version = None
                        if install_info:
                            version = install_info.get("version", None)
                        if not version:
                            version = "(unknown version)"
                        self.display("- %s, %s" % (path_file, version))
        return 0

    def execute_search(self):
        ''' searches for roles on the Ansible Galaxy server'''
        page_size = 1000
        search = None

        if len(self.args):
            terms = []
            for i in range(len(self.args)):
                terms.append(self.args.pop())
            search = '+'.join(terms[::-1])

        if not search and not self.options.platforms and not self.options.galaxy_tags and not self.options.author:
            raise cli_exceptions.GalaxyCliError("Invalid query. At least one search term, platform, galaxy tag or author must be provided.")

        response = self.api.search_roles(search, platforms=self.options.platforms,
                                         tags=self.options.galaxy_tags, author=self.options.author, page_size=page_size)

        if response['count'] == 0:
            self.display("No roles match your search.")
            return True

        data = [u'']

        if response['count'] > page_size:
            data.append(u"Found %d roles matching your search. Showing first %s." % (response['count'], page_size))
        else:
            data.append(u"Found %d roles matching your search:" % response['count'])

        max_len = []
        for role in response['results']:
            max_len.append(len(role['username'] + '.' + role['name']))
        name_len = max(max_len)
        format_str = u" %%-%ds %%s" % name_len
        data.append(u'')
        data.append(format_str % (u"Name", u"Description"))
        data.append(format_str % (u"----", u"-----------"))
        for role in response['results']:
            data.append(format_str % (u'%s.%s' % (role['username'], role['name']), role['description']))

        data = u'\n'.join(data)
        self.display(data)
        return True

    def execute_login(self):
        """
        verify user's identify via Github and retrieve an auth token from Ansible Galaxy.
        """
        # Authenticate with github and retrieve a token
        if self.options.token is None:
            if runtime.GALAXY_TOKEN:
                github_token = runtime.GALAXY_TOKEN
            else:
                login = GalaxyLogin(self.galaxy)
                github_token = login.create_github_token()
        else:
            github_token = self.options.token

        galaxy_response = self.api.authenticate(github_token)

        if self.options.token is None and runtime.GALAXY_TOKEN is None:
            # Remove the token we created
            login.remove_github_token()

        # Store the Galaxy token
        token = GalaxyToken()
        token.set(galaxy_response['token'])

        self.display("Successfully logged into Galaxy as %s" % galaxy_response['username'])
        return 0

    def execute_import(self):
        """ used to import a role into Ansible Galaxy """

        # FIXME/TODO(alikins): replace with logging or display callback
        colors = {
            'INFO': 'normal',
            'WARNING': runtime.COLOR_WARN,
            'ERROR': runtime.COLOR_ERROR,
            'SUCCESS': runtime.COLOR_OK,
            'FAILED': runtime.COLOR_ERROR,
            'DEBUG': runtime.COLOR_DEBUG,
        }

        if len(self.args) < 2:
            raise cli_exceptions.GalaxyCliError("Expected a github_username and github_repository. Use --help.")

        github_repo = to_text(self.args.pop(), errors='surrogate_or_strict')
        github_user = to_text(self.args.pop(), errors='surrogate_or_strict')

        if self.options.check_status:
            task = self.api.get_import_task(github_user=github_user, github_repo=github_repo)
        else:
            # Submit an import request
            task = self.api.create_import_task(github_user, github_repo, reference=self.options.reference, role_name=self.options.role_name)

            if len(task) > 1:
                # found multiple roles associated with github_user/github_repo
                self.display("WARNING: More than one Galaxy role associated with Github repo %s/%s." % (github_user, github_repo),
                             color='yellow')
                self.display("The following Galaxy roles are being updated:" + u'\n', color=runtime.COLOR_CHANGED)
                for t in task:
                    self.display('%s.%s' % (t['summary_fields']['role']['namespace'], t['summary_fields']['role']['name']), color=runtime.COLOR_CHANGED)
                    self.display(u'\nTo properly namespace this role, remove each of the above and re-import %s/%s from scratch' % (github_user, github_repo),
                                 color=runtime.COLOR_CHANGED)
                return 0
            # found a single role as expected
            self.display("Successfully submitted import request %d" % task[0]['id'])
            if not self.options.wait:
                self.display("Role name: %s" % task[0]['summary_fields']['role']['name'])
                self.display("Repo: %s/%s" % (task[0]['github_user'], task[0]['github_repo']))

        if self.options.check_status or self.options.wait:
            # Get the status of the import
            msg_list = []
            finished = False
            while not finished:
                task = self.api.get_import_task(task_id=task[0]['id'])
                for msg in task[0]['summary_fields']['task_messages']:
                    if msg['id'] not in msg_list:
                        self.display(msg['message_text'], color=colors[msg['message_type']])
                        msg_list.append(msg['id'])
                if task[0]['state'] in ['SUCCESS', 'FAILED']:
                    finished = True
                else:
                    time.sleep(10)

        return 0

    def execute_setup(self):
        """ Setup an integration from Github or Travis for Ansible Galaxy roles"""

        if self.options.setup_list:
            # List existing integration secrets
            secrets = self.api.list_secrets()
            if len(secrets) == 0:
                # None found
                self.display("No integrations found.")
                return 0
            self.display(u'\n' + "ID         Source     Repo", color=runtime.COLOR_OK)
            self.display("---------- ---------- ----------", color=runtime.COLOR_OK)
            for secret in secrets:
                self.display("%-10s %-10s %s/%s" % (secret['id'], secret['source'], secret['github_user'],
                                                    secret['github_repo']), color=runtime.COLOR_OK)
            return 0

        if self.options.remove_id:
            # Remove a secret
            self.api.remove_secret(self.options.remove_id)
            self.display("Secret removed. Integrations using this secret will not longer work.", color=runtime.COLOR_OK)
            return 0

        if len(self.args) < 4:
            raise cli_exceptions.GalaxyCliError("Missing one or more arguments. Expecting: source github_user github_repo secret")

        secret = self.args.pop()
        github_repo = self.args.pop()
        github_user = self.args.pop()
        source = self.args.pop()

        resp = self.api.add_secret(source, github_user, github_repo, secret)
        self.display("Added integration for %s %s/%s" % (resp['source'], resp['github_user'], resp['github_repo']))

        return 0

    def execute_delete(self):
        """ Delete a role from Ansible Galaxy. """

        if len(self.args) < 2:
            raise cli_exceptions.GalaxyCliError("Missing one or more arguments. Expected: github_user github_repo")

        github_repo = self.args.pop()
        github_user = self.args.pop()
        resp = self.api.delete_role(github_user, github_repo)

        if len(resp['deleted_roles']) > 1:
            self.display("Deleted the following roles:")
            self.display("ID     User            Name")
            self.display("------ --------------- ----------")
            for role in resp['deleted_roles']:
                self.display("%-8s %-15s %s" % (role.id, role.namespace, role.name))

        self.display(resp['status'])

        return True
