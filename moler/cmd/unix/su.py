# -*- coding: utf-8 -*-
"""
Su command module.
"""

__author__ = 'Agnieszka Bylica, Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'agnieszka.bylica@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'

import re

from moler.cmd.commandtextualgeneric import CommandTextualGeneric
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone


class Su(GenericUnixCommand):

    def __init__(self, connection, login=None, options=None, password=None, prompt=None, expected_prompt=None,
                 newline_chars=None, encrypt_password=True, target_newline="\n", runner=None, set_timeout=None,
                 allowed_newline_after_prompt=False, set_prompt=None):
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
        """
        super(Su, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)

        # Parameters defined by calling the command
        self.expected_prompt = expected_prompt
        self._re_expected_prompt = CommandTextualGeneric._calculate_prompt(expected_prompt)  # Expected prompt on device
        self.login = login
        self.options = options
        self.password = password
        self.encrypt_password = encrypt_password
        self.target_newline = target_newline
        self.set_timeout = set_timeout
        self.allowed_newline_after_prompt = allowed_newline_after_prompt
        self.set_prompt = set_prompt

        # Internal variables
        self._password_sent = False
        self.current_ret['RESULT'] = list()

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.

        :return: String representation of command to send over connection to device.
        """
        cmd = "su"
        if self.options:
            cmd = cmd + " " + self.options
        if self.login:
            cmd = cmd + " " + self.login
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Parses the output of the command.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise.
        :return: None.
        """
        try:
            self._send_password_if_requested(line)
            if is_full_line:
                self._command_failure(line)
                self._authentication_failure(line)
                self._parse(line)
            elif self._is_prompt(line):
                if not self.done():
                    self.set_result({})
        except ParsingDone:
            pass

        return super(Su, self).on_new_line(line, is_full_line)

    _re_authentication_fail = re.compile(r"su:\sAuthentication\sfailure(?P<AUTH>.*)"
                                         r"|su:\sPermission denied\s(?P<PERM>.*)"
                                         r"|su:\sincorrect password\s(?P<PASS>.*)", re.IGNORECASE)

    def _authentication_failure(self, line):
        """
        Checks if line has info about authentication failure.

        :param line: Line from device.
        :return: Nothing but raises ParsingDone if regex matches.
        """
        if self._regex_helper.search_compiled(Su._re_authentication_fail, line):
            self.set_exception(CommandFailure(self, "ERROR: {}, {}, {}".format(self._regex_helper.group("AUTH"),
                                                                               self._regex_helper.group("PERM"),
                                                                               self._regex_helper.group("PASS"))))

            raise ParsingDone

    _re_command_fail = re.compile(r"su:\s(invalid|unrecognized)\soption\s(?P<OPTION>.*)", re.IGNORECASE)
    _re_wrong_username = re.compile(r"No\spasswd\sentry\sfor\suser\s(?P<USERNAME>.*)", re.IGNORECASE)

    def _command_failure(self, line):
        """
        Checks if line has info about command failure.

        :param line: Line from device.
        :return: Nothing but raises ParsingDone if regex matches.
        """
        if self._regex_helper.search_compiled(Su._re_command_fail, line):
            self.set_exception(CommandFailure(self, "ERROR: {}".format(self._regex_helper.group("OPTION"))))
            raise ParsingDone
        elif self._regex_helper.search_compiled(Su._re_wrong_username, line):
            self.set_exception(CommandFailure(self, "ERROR: {}".format(self._regex_helper.group("USERNAME"))))
            raise ParsingDone

    _re_password = re.compile(r"Password:", re.IGNORECASE)

    def _is_password_requested(self, line):
        """
        Checks if device waits for password.

        :param line: Line from device.
        :return: Match object if regex matches, None otherwise.
        """
        return self._regex_helper.search_compiled(Su._re_password, line)

    def _is_prompt(self, line):
        """
        Checks if device sends final prompt.

        :param line: Line from device.
        :return: Match object if regex matches, None otherwise
        """
        if self.expected_prompt:
            return self._regex_helper.search_compiled(self._re_expected_prompt, line)
        return None

    def _send_password_if_requested(self, line):
        """
        Sends password.

        :param line: Line from device.
        :return: Nothing but raises ParsingDone if regex matches.
        """
        if (not self._password_sent) and self._is_password_requested(line) and self.password:
            self.connection.sendline(self.password, encrypt=self.encrypt_password)
            self._password_sent = True
            raise ParsingDone
        elif (not self._password_sent) and self._is_password_requested(line) and (not self.password):
            self.connection.sendline('')
            raise ParsingDone

    def _parse(self, line):
        """
        Add output to result.

        :param line: Line from device
        :return: Nothing but raises ParsingDone
        """
        self.current_ret['RESULT'].append(line)
        raise ParsingDone


COMMAND_OUTPUT_su = """
xyz@debian:~$ su
Password:
root@debian:/home/xyz#"""

COMMAND_KWARGS_su = {
    'login': None, 'options': None, 'password': '1234', 'expected_prompt': 'root@debian:/home/xyz#'
}

COMMAND_RESULT_su = {}

COMMAND_OUTPUT_su_option = """
xyz@debian:~$ su -c 'ls' xyz
Password:
Dokumenty Pobrane Publiczny Pulpit Szablony Wideo
xyz@debian:~$"""

COMMAND_KWARGS_su_option = {
    'login': 'xyz', 'options': "-c 'ls'", 'password': '1234'
}

COMMAND_RESULT_su_option = {'RESULT': ['Dokumenty Pobrane Publiczny Pulpit Szablony Wideo']}
