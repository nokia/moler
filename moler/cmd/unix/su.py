# -*- coding: utf-8 -*-
"""
Su command module.
"""

__author__ = 'Agnieszka Bylica, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'agnieszka.bylica@nokia.com, marcin.usielski@nokia.com'

import re

from moler.cmd.commandtextualgeneric import CommandTextualGeneric
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone


class Su(GenericUnixCommand):

    def __init__(self, connection, user=None, options=None, password=None, prompt=None, expected_prompt=None,
                 newline_chars=None, encrypt_password=True, runner=None):
        super(Su, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)

        # Parameters defined by calling the command
        self.expected_prompt = expected_prompt
        self._re_expected_prompt = None             # Expected prompt on device
        self.user = user
        self.options = options
        self.password = password
        self.encrypt_password = encrypt_password

        # Internal variables
        self._password_sent = False
        self.current_ret['RESULT'] = list()

    def build_command_string(self):
        cmd = "su"
        if self.options:
            cmd = cmd + " " + self.options
        if self.user:
            cmd = cmd + " " + self.user
        return cmd

    def on_new_line(self, line, is_full_line):
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
        if self._regex_helper.search_compiled(Su._re_authentication_fail, line):
            self.set_exception(CommandFailure(self, "ERROR: {}, {}, {}".format(self._regex_helper.group("AUTH"),
                                                                               self._regex_helper.group("PERM"),
                                                                               self._regex_helper.group("PASS"))))

            raise ParsingDone

    _re_command_fail = re.compile(r"su:\s(invalid|unrecognized)\soption\s(?P<OPTION>.*)", re.IGNORECASE)
    _re_wrong_username = re.compile(r"No\spasswd\sentry\sfor\suser\s(?P<USERNAME>.*)", re.IGNORECASE)

    def _command_failure(self, line):
        if self._regex_helper.search_compiled(Su._re_command_fail, line):
            self.set_exception(CommandFailure(self, "ERROR: {}".format(self._regex_helper.group("OPTION"))))
            raise ParsingDone
        elif self._regex_helper.search_compiled(Su._re_wrong_username, line):
            self.set_exception(CommandFailure(self, "ERROR: {}".format(self._regex_helper.group("USERNAME"))))
            raise ParsingDone

    _re_password = re.compile(r"Password:", re.IGNORECASE)

    def _is_password_requested(self, line):
        return self._regex_helper.search_compiled(Su._re_password, line)

    def _is_prompt(self, line):
        if self.expected_prompt:
            self._re_expected_prompt = CommandTextualGeneric._calculate_prompt(self.expected_prompt)
            return self._regex_helper.search_compiled(self._re_expected_prompt, line)
        return False

    def _send_password_if_requested(self, line):
        if (not self._password_sent) and self._is_password_requested(line) and self.password:
            self.connection.sendline(self.password, encrypt=self.encrypt_password)
            self._password_sent = True
            raise ParsingDone
        elif (not self._password_sent) and self._is_password_requested(line) and (not self.password):
            self.connection.sendline('')
            raise ParsingDone

    def _parse(self, line):
        self.current_ret['RESULT'].append(line)
        raise ParsingDone


COMMAND_OUTPUT_su = """
xyz@debian:~$ su
Password:
root@debian:/home/xyz#"""

COMMAND_KWARGS_su = {
    'user': None, 'options': None, 'password': '1234', 'expected_prompt': 'root@debian:/home/xyz#'
}

COMMAND_RESULT_su = {}

COMMAND_OUTPUT_su_option = """
xyz@debian:~$ su -c 'ls' xyz
Password:
Dokumenty Pobrane Publiczny Pulpit Szablony Wideo
xyz@debian:~$"""

COMMAND_KWARGS_su_option = {
    'user': 'xyz', 'options': "-c 'ls'", 'password': '1234'
}

COMMAND_RESULT_su_option = {'RESULT': ['Dokumenty Pobrane Publiczny Pulpit Szablony Wideo']}
