# -*- coding: utf-8 -*-
"""
Su command module.
"""

__author__ = 'Agnieszka Bylica, Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018-2020, Nokia'
__email__ = 'agnieszka.bylica@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'

import re

from moler.cmd.unix.sudo import Sudo
from moler.exceptions import CommandFailure


class Su(Sudo):

    def __init__(self, connection, login=None, options=None, password=None, prompt=None, expected_prompt=None,
                 newline_chars=None, encrypt_password=True, target_newline="\n", runner=None, set_timeout=None,
                 allowed_newline_after_prompt=False, set_prompt=None, prompt_after_login=None, cmd_object=None,
                 cmd_class_name=None, cmd_params=None):
        """
        Moler class of Unix command su.

        :param connection: moler connection to device, terminal when command is executed.
        :param login: user name.
        :param options: su unix command options.
        :param password: password.
        :param prompt: start prompt.
        :param expected_prompt: final prompt.
        :param newline_chars: Characters to split lines.
        :param encrypt_password: If True then * will be in logs when password is sent, otherwise plain text.
        :param target_newline: newline chars on root user.
        :param runner: Runner to run command.
        :param set_timeout: Command to set timeout after su success.
        :param allowed_newline_after_prompt: If True then newline chars may occur after expected (target) prompt
        :param set_prompt: Command to set prompt after su success.
        :param prompt_after_login: prompt after login before send export PS1. If you do not change prompt exporting PS1
         then leave it None.
        :param cmd_object: object of command. Pass this object or cmd_class_name.
        :param cmd_class_name: full (with package) class name. Pass this name or cmd_object.
        :param cmd_params: params for cmd_class_name. If cmd_object is passed this parameter is ignored.
        """

        super(Su, self).__init__(connection=connection, password=password, cmd_object=cmd_object,
                                 cmd_class_name=cmd_class_name, cmd_params=cmd_params, prompt=prompt,
                                 newline_chars=newline_chars, runner=runner, encrypt_password=encrypt_password,
                                 expected_prompt=expected_prompt, set_timeout=set_timeout, set_prompt=set_prompt,
                                 target_newline=target_newline,
                                 allowed_newline_after_prompt=allowed_newline_after_prompt,
                                 prompt_after_login=prompt_after_login)

        # Parameters defined by calling the command
        self.options = options
        self.login = login

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.

        :return: String representation of command to send over connection to device.
        """
        self._build_command_object()
        cmd = "su"
        if self.options:
            cmd = "{} {}".format(cmd, self.options)
        if self.cmd_object:
            cmd = "{} -c '{}'".format(cmd, self.cmd_object.command_string)
        if self.login:
            cmd = "{} {}".format(cmd, self.login)
        return cmd

    def _validate_passed_object_or_command_parameters(self):
        """
        Validates passed parameters to create embedded command object.

        :return: None
        :raise: CommandFailure if command parameters are wrong.
        """
        if self._validated_embedded_parameters:
            return  # Validate parameters only once
        if self.cmd_object and self.cmd_class_name:
            # _validate_start is called before running command on connection, so we raise exception instead
            # of setting it
            raise CommandFailure(
                self,
                "Both 'cmd_object' and 'cmd_class_name' parameters were provided. Please specify only one."
            )
        if self.cmd_object and self.cmd_object.done():
            # _validate_start is called before running command on connection, so we raise exception
            # instead of setting it
            raise CommandFailure(
                self,
                "Not allowed to run again the embedded command (embedded command is done): {}.".format(
                    self.cmd_object))
        if not self.cmd_object:
            self._finish_on_final_prompt = True
        self._validated_embedded_parameters = True

    # password:
    _re_su_password = re.compile(r"^\s*password*:", re.I)

    def _get_password_regex(self):
        return Su._re_su_password

    # su: Authentication failure
    _re_su_wrong_password = re.compile(r"su: Authentication failure", re.I)

    def _get_wrong_password_regex(self):
        return Su._re_su_wrong_password

    # No passwd entry for user
    _re_su_error = re.compile(
        r"No passwd entry for user|su:\s+(invalid|unrecognized)\s+option|usage:\s+su|su:\s+not found",
        re.I)

    def _get_error_regex(self):
        return Su._re_su_error


COMMAND_OUTPUT_su = """
xyz@debian:~$ su
Password:
root@debian:/home/xyz#"""

COMMAND_KWARGS_su = {
    'login': None, 'options': None, 'password': '1234', 'expected_prompt': 'root@debian:/home/xyz#'
}

COMMAND_RESULT_su = {}

COMMAND_OUTPUT_su_option = """ su -c 'ls' xyz
Password:
Dokumenty Pobrane Publiczny Pulpit Szablony Wideo
xyz@debian:~$"""

COMMAND_KWARGS_su_option = {
    'login': 'xyz', 'cmd_class_name': 'moler.cmd.unix.ls.Ls', 'password': '1234'
}

COMMAND_RESULT_su_option = {
    'files': {
        'Dokumenty': {'name': 'Dokumenty'},
        'Pobrane': {'name': 'Pobrane'},
        'Publiczny': {'name': 'Publiczny'},
        'Pulpit': {'name': 'Pulpit'},
        'Szablony': {'name': 'Szablony'},
        'Wideo': {'name': 'Wideo'}
    }
}

COMMAND_OUTPUT_newline_after_prompt = """
xyz@debian:~$ su
Password:
root@debian:/home/xyz#
"""

COMMAND_KWARGS_newline_after_prompt = {
    'login': None, 'options': None, 'password': '1234', 'expected_prompt': 'root@debian:/home/xyz#',
    'allowed_newline_after_prompt': True
}

COMMAND_RESULT_newline_after_prompt = {}

COMMAND_OUTPUT_newline_after_prompt_with_prompt_change = """
xyz@debian:~$ su
Password:
root@debian:/home/xyz
$ export PS1="${PS1::-4} #
root@debian:/home/xyz #
"""

COMMAND_KWARGS_newline_after_prompt_with_prompt_change = {
    'login': None, 'options': None, 'password': '1234', 'expected_prompt': 'root@debian:/home/xyz',
    'allowed_newline_after_prompt': True, 'set_prompt': r'export PS1="${PS1::-4} #"',
}

COMMAND_RESULT_newline_after_prompt_with_prompt_change = {}

COMMAND_OUTPUT_set_timeout = """
xyz@debian:~$ su
Password:
root@debian:/home/xyz# export TMOUT="2678400"
root@debian:/home/xyz# """

COMMAND_KWARGS_set_timeout = {
    'login': None, 'options': None, 'password': '1234', 'expected_prompt': 'root@debian:/home/xyz#',
    'set_timeout': r'export TMOUT="2678400"',
}

COMMAND_RESULT_set_timeout = {}
