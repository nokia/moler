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
        self._sent_password = False
        self._sent_timeout = False
        self._sent_prompt = False
        self.current_ret = dict()
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
            self._commands_after_established(line, is_full_line)
            self._detect_prompt_after_exception(line)
            self._authentication_failure(line)
            self._command_failure(line)
            if is_full_line:
                self._sent_password = False  # Clear flag for multi passwords connections
                self._parse(line)
        except ParsingDone:
            pass

    def _detect_prompt_after_exception(self, line):
        """
        Detects start prompt.

        :param line: Line from device.
        :return: Nothing but raises ParsingDone if detects start prompt and any exception was set.
        """
        if self._stored_exception and self._regex_helper.search_compiled(self._re_prompt, line):
            self._is_done = True
            raise ParsingDone()

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

    def _commands_after_established(self, line, is_full_line):
        """
        Performs commands after su connection is established and user is logged in.

        :param line: Line from device.
        :param is_full_line: True is line contained new line chars, False otherwise.
        :return: Nothing but raises ParsingDone if all required commands are sent.
        """
        sent = self._send_after_login_settings(line)
        if sent:
            raise ParsingDone()
        if (not sent) and self._is_target_prompt(line):
            if not is_full_line or self.allowed_newline_after_prompt:
                if self._all_after_login_settings_sent() or self._no_after_login_settings_needed():
                    if not self.done():
                        self.set_result(self.current_ret)
                    raise ParsingDone()

    def _timeout_set_needed(self):
        """
        Checks if command for timeout is awaited.

        :return: True if command is set and not sent. False otherwise.
        """
        return self.set_timeout and not self._sent_timeout

    def _send_timeout_set(self):
        """
        Sends command to set timeout.

        :return: Nothing.
        """
        cmd = "{}{}{}".format(self.target_newline, self.set_timeout, self.target_newline)
        self.connection.send(cmd)
        self._sent_timeout = True

    def _prompt_set_needed(self):
        """
        Checks if command for prompt is awaited.

        :return: True if command is set and not sent. False otherwise.
        """
        return self.set_prompt and not self._sent_prompt

    def _send_prompt_set(self):
        """
        Sends command to set prompt.

        :return: Nothing.
        """
        cmd = "{}{}{}".format(self.target_newline, self.set_prompt, self.target_newline)
        self.connection.send(cmd)
        self._sent_prompt = True

    def _all_after_login_settings_sent(self):
        """
        Checks if all requested commands are sent.

        :return: True if all commands after ssh connection establishing are sent, False otherwise
        """
        both_requested = self.set_prompt and self.set_timeout
        both_sent = self._sent_prompt and self._sent_timeout
        single_req_and_sent1 = self.set_prompt and self._sent_prompt
        single_req_and_sent2 = self.set_timeout and self._sent_timeout
        return (both_requested and both_sent) or single_req_and_sent1 or single_req_and_sent2

    def _no_after_login_settings_needed(self):
        """
        Checks if any commands after logged in are requested.

        :return: True if no commands are awaited, False if any.
        """
        return (not self.set_prompt) and (not self.set_timeout)

    def _is_target_prompt(self, line):
        """
        Checks if device sends prompt from target system.

        :param line: Line from device.
        :return: Match object if regex matches, None otherwise.
        """
        return self._regex_helper.search_compiled(self._re_expected_prompt, line)

    def _send_after_login_settings(self, line):
        """
        Sends information about timeout and prompt.

        :param line: Line from device.
        :return: True if anything was sent, False otherwise.
        """
        if self._is_target_prompt(line):
            if self._timeout_set_needed():
                self._send_timeout_set()
                return True  # just sent
            elif self._prompt_set_needed():
                self._send_prompt_set()
                return True  # just sent
        return False  # nothing sent

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

    def _send_password_if_requested(self, line):
        """
        Sends password.

        :param line: Line from device.
        :return: Nothing but raises ParsingDone if regex matches.
        """
        if (not self._sent_password) and self._is_password_requested(line) and self.password:
            self.connection.sendline(self.password, encrypt=self.encrypt_password)
            self._sent_password = True
            raise ParsingDone
        elif (not self._sent_password) and self._is_password_requested(line) and (not self.password):
            self.connection.sendline('')
            raise ParsingDone

    def _parse(self, line):
        """
        Add output to result.

        :param line: Line from device
        :return: Nothing but raises ParsingDone
        """
        self.current_ret['RESULT'].append(line)
        raise ParsingDone()


COMMAND_OUTPUT_su = """
xyz@debian:~$ su
Password:
root@debian:/home/xyz#"""

COMMAND_KWARGS_su = {
    'login': None, 'options': None, 'password': '1234', 'expected_prompt': 'root@debian:/home/xyz#'
}

COMMAND_RESULT_su = {'RESULT': []}

COMMAND_OUTPUT_su_option = """
xyz@debian:~$ su -c 'ls' xyz
Password:
Dokumenty Pobrane Publiczny Pulpit Szablony Wideo
xyz@debian:~$"""

COMMAND_KWARGS_su_option = {
    'login': 'xyz', 'options': "-c 'ls'", 'password': '1234'
}

COMMAND_RESULT_su_option = {'RESULT': ['Dokumenty Pobrane Publiczny Pulpit Szablony Wideo']}

COMMAND_OUTPUT_newline_after_prompt = """
xyz@debian:~$ su
Password:
root@debian:/home/xyz#
"""

COMMAND_KWARGS_newline_after_prompt = {
    'login': None, 'options': None, 'password': '1234', 'expected_prompt': 'root@debian:/home/xyz#',
    'allowed_newline_after_prompt': True
}

COMMAND_RESULT_newline_after_prompt = {'RESULT': []}

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

COMMAND_RESULT_newline_after_prompt_with_prompt_change = {'RESULT': [r'$ export PS1="${PS1::-4} #']}

COMMAND_OUTPUT_set_timeout = """
xyz@debian:~$ su
Password:
root@debian:/home/xyz# export TMOUT="2678400"
root@debian:/home/xyz# """

COMMAND_KWARGS_set_timeout = {
    'login': None, 'options': None, 'password': '1234', 'expected_prompt': 'root@debian:/home/xyz#',
    'set_timeout': r'export TMOUT="2678400"',
}

COMMAND_RESULT_set_timeout = {'RESULT': []}
