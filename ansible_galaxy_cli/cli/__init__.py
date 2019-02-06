# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2016, Toshio Kuratomi <tkuratomi@ansible.com>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import logging
import operator
import optparse
import re
import six

from abc import ABCMeta, abstractmethod

from ansible_galaxy.config import defaults
from ansible_galaxy import display
from ansible_galaxy.utils.text import to_text
from ansible_galaxy_cli import exceptions as cli_exceptions

log = logging.getLogger(__name__)


class SortedOptParser(optparse.OptionParser):
    '''Optparser which sorts the options by opt before outputting --help'''

    def format_help(self, formatter=None):
        self.option_list.sort(key=operator.methodcaller('get_opt_string'))
        return optparse.OptionParser.format_help(self, formatter=None)


# Note: Inherit from SortedOptParser so that we get our format_help method
class InvalidOptsParser(SortedOptParser):
    '''Ignore invalid options.

    Meant for the special case where we need to take care of help and version
    but may not know the full range of options yet.  (See it in use in set_action)
    '''

    def __init__(self, parser):
        # Since this is special purposed to just handle help and version, we
        # take a pre-existing option parser here and set our options from
        # that.  This allows us to give accurate help based on the given
        # option parser.
        SortedOptParser.__init__(self, usage=parser.usage,
                                 option_list=parser.option_list,
                                 option_class=parser.option_class,
                                 conflict_handler=parser.conflict_handler,
                                 description=parser.description,
                                 formatter=parser.formatter,
                                 add_help_option=False,
                                 prog=parser.prog,
                                 epilog=parser.epilog)
        self.version = parser.version

    def _process_long_opt(self, rargs, values):
        try:
            optparse.OptionParser._process_long_opt(self, rargs, values)
        except optparse.BadOptionError:
            pass

    def _process_short_opts(self, rargs, values):
        try:
            optparse.OptionParser._process_short_opts(self, rargs, values)
        except optparse.BadOptionError:
            pass


class CLI(six.with_metaclass(ABCMeta, object)):
    ''' code behind bin/ansible* programs '''

    VALID_ACTIONS = []
    VALID_ACTION_ALIASES = {}

    _ITALIC = re.compile(r"I\(([^)]+)\)")
    _BOLD = re.compile(r"B\(([^)]+)\)")
    _MODULE = re.compile(r"M\(([^)]+)\)")
    _URL = re.compile(r"U\(([^)]+)\)")
    _CONST = re.compile(r"C\(([^)]+)\)")

    PAGER = 'less'

    # -F (quit-if-one-screen) -R (allow raw ansi control chars)
    # -S (chop long lines) -X (disable termcap init and de-init)
    LESS_OPTS = 'FRSX'
    SKIP_INVENTORY_DEFAULTS = False

    def __init__(self, args, callback=None):
        """
        Base init method for all command line programs
        """

        self.args = args
        self._orig_args_copy = self.args[:]
        self.options = None
        self.parser = None
        self.action = None
        self.callback = callback
        self.log = logging.getLogger(__name__ + '.' + self.__class__.__name__)
        self.config_file_path = None

    def set_action(self):
        """
        Get the action the user wants to execute from the sys argv list.
        """
        for i in range(0, len(self.args)):
            arg = self.args[i]
            if arg in self.VALID_ACTIONS:
                self.action = arg
                del self.args[i]
                break
            if arg in self.VALID_ACTION_ALIASES:
                self.action = self.VALID_ACTION_ALIASES[arg]
                del self.args[i]
                break

        if not self.action:
            # if we're asked for help or version, we don't need an action.
            # have to use a special purpose Option Parser to figure that out as
            # the standard OptionParser throws an error for unknown options and
            # without knowing action, we only know of a subset of the options
            # that could be legal for this command
            tmp_parser = InvalidOptsParser(self.parser)
            tmp_options, _ = tmp_parser.parse_args(self.args)
            if not(hasattr(tmp_options, 'help') and tmp_options.help) or (hasattr(tmp_options, 'version') and tmp_options.version):
                raise cli_exceptions.CliOptionsError("Missing required action")

    def execute(self):
        """
        Actually runs a child defined method using the execute_<action> pattern
        """
        if '-' in self.action:
            # Call a function named execute_some_action if the action is some-action
            fn = getattr(self, "execute_%s" % self.action.replace('-', '_'))
        else:
            fn = getattr(self, "execute_%s" % self.action)
        return fn()

    @abstractmethod
    def run(self):
        """Run the ansible command

        Subclasses must implement this method.  It does the actual work of
        running an Ansible command.
        """
        log.debug('self.args: %s', self.args)

        if self.config_file_path:
            log.info(u"Using %s as config file", to_text(self.config_file_path))
        else:
            log.info(u"No config file found; using defaults")

    def validate_conflicts(self, vault_opts=False, runas_opts=False, fork_opts=False, vault_rekey_opts=False):
        ''' check for conflicting options '''

        op = self.options

        if vault_opts:
            # Check for vault related conflicts
            if (op.ask_vault_pass and op.vault_password_files):
                self.parser.error("--ask-vault-pass and --vault-password-file are mutually exclusive")

        if vault_rekey_opts:
            if (op.new_vault_id and op.new_vault_password_file):
                self.parser.error("--new-vault-password-file and --new-vault-id are mutually exclusive")

        if runas_opts:
            # Check for privilege escalation conflicts
            if ((op.su or op.su_user) and (op.sudo or op.sudo_user) or
                    (op.su or op.su_user) and (op.become or op.become_user) or
                    (op.sudo or op.sudo_user) and (op.become or op.become_user)):

                self.parser.error("Sudo arguments ('--sudo', '--sudo-user', and '--ask-sudo-pass') and su arguments ('--su', '--su-user', and '--ask-su-pass') "
                                  "and become arguments ('--become', '--become-user', and '--ask-become-pass') are exclusive of each other")

        if fork_opts:
            if op.forks < 1:
                self.parser.error("The number of processes (--forks) must be >= 1")

    @staticmethod
    def base_parser(usage="", output_opts=False, runas_opts=False, meta_opts=False, runtask_opts=False, vault_opts=False, module_opts=False,
                    async_opts=False, connect_opts=False, subset_opts=False, check_opts=False, inventory_opts=False, epilog=None, fork_opts=False,
                    runas_prompt_opts=False, desc=None, basedir_opts=False, vault_rekey_opts=False):
        ''' create an options parser for most ansible scripts '''

        # base opts
        parser = SortedOptParser(usage,  description=desc, epilog=epilog)
        parser.add_option('-v', '--verbose', dest='verbosity', default=defaults.VERBOSITY, action="count",
                          help="verbose mode (-vvv for more, -vvvv to enable connection debugging)")

        return parser

    @abstractmethod
    def parse(self):
        """Parse the command line args

        This method parses the command line arguments.  It uses the parser
        stored in the self.parser attribute and saves the args and options in
        self.args and self.options respectively.

        Subclasses need to implement this method.  They will usually create
        a base_parser, add their own options to the base_parser, and then call
        this method to do the actual parsing.  An implementation will look
        something like this::

            def parse(self):
                parser = super(MyCLI, self).base_parser(usage="My Ansible CLI", inventory_opts=True)
                parser.add_option('--my-option', dest='my_option', action='store')
                self.parser = parser
                super(MyCLI, self).parse()
                # If some additional transformations are needed for the
                # arguments and options, do it here.
        """

        self.options, self.args = self.parser.parse_args(self.args[1:])
        # process inventory options except for CLIs that require their own processing

    # FIXME: replace with output callback
    def display(self, *args, **kwargs):
        kwargs.pop('color', None)
        display.display_callback(*args, **kwargs)

    @classmethod
    def tty_ify(cls, text):

        t = cls._ITALIC.sub("`" + r"\1" + "'", text)    # I(word) => `word'
        t = cls._BOLD.sub("*" + r"\1" + "*", t)         # B(word) => *word*
        t = cls._MODULE.sub("[" + r"\1" + "]", t)       # M(word) => [word]
        t = cls._URL.sub(r"\1", t)                      # U(word) => word
        t = cls._CONST.sub("`" + r"\1" + "'", t)        # C(word) => `word'

        return t
