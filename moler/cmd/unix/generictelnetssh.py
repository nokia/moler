# -*- coding: utf-8 -*-
"""
Base class for telnet and ssh commands.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2019-2020, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import re
import six
import abc

from moler.cmd.commandtextualgeneric import CommandTextualGeneric
from moler.cmd.commandchangingprompt import CommandChangingPrompt
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone
from moler.helpers import copy_list
from dateutil import parser
from moler.util.converterhelper import ConverterHelper


@six.add_metaclass(abc.ABCMeta)
class GenericTelnetSsh(CommandChangingPrompt):
    # Compiled regexp

    # Login:
    _re_login = re.compile(r"login:\s*$", re.IGNORECASE)

    # Password:
    _re_password = re.compile(r"password:", re.IGNORECASE)

    # Permission denied.
    _re_failed_strings = re.compile(
        r"Permission denied|closed by foreign host|telnet:.*Name or service not known|No route to host|ssh: Could not|"
        "is not a typo you can use command-not-found to lookup the package|command not found|"
        "Too many authentication failures|Received disconnect from|Authentication failed",
        re.IGNORECASE)

    # CLIENT5 [] has just connected!
    _re_has_just_connected = re.compile(r"has just connected|\{bash_history,ssh\}|Escape character is", re.IGNORECASE)

    def __init__(self, connection, host, login=None, password=None, newline_chars=None, prompt=None, runner=None,
                 port=0, expected_prompt=r'^>\s*', set_timeout=r'export TMOUT=\"2678400\"', set_prompt=None,
                 term_mono="TERM=xterm-mono", encrypt_password=True, target_newline="\n",
                 allowed_newline_after_prompt=False, repeat_password=True, failure_exceptions_indication=None,
                 prompt_after_login=None, send_enter_after_connection=True, username=None):
        """
        Base Moler class of Unix commands telnet and ssh.

        :param connection: moler connection to device, terminal when command is executed.
        :param host: address of telnet server.
        :param login: login to telnet server.
        :param password: password to telnet server.
        :param port: port to listen on server.
        :param prompt: prompt on start system (where command telnet starts).
        :param expected_prompt: prompt on server (where command telnet connects).
        :param set_timeout: Command to set timeout after telnet connects.
        :param set_prompt: Command to set prompt after telnet connects.
        :param term_mono: Params to set ssh mono connection (useful in script).
        :param newline_chars: characters to split lines.
        :param encrypt_password: If True then * will be in logs when password is sent, otherwise plain text.
        :param runner: Runner to run command.
        :param target_newline: newline chars on remote system where ssh connects.
        :param allowed_newline_after_prompt: If True then newline chars may occur after expected (target) prompt.
        :param repeat_password: If True then repeat last password if no more provided. If False then exception is set.
        :param failure_exceptions_indication: String with regex or regex object to omit failure even if failed string
         was found.
        :param prompt_after_login: prompt after login before send export PS1. If you do not change prompt exporting PS1
         then leave it None.
        :param send_enter_after_connection: set True to send new line char(s) after connection is established, False
         otherwise.
        """
        super(GenericTelnetSsh, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                               runner=runner, expected_prompt=expected_prompt, set_timeout=set_timeout,
                                               set_prompt=set_prompt, target_newline=target_newline,
                                               allowed_newline_after_prompt=allowed_newline_after_prompt,
                                               prompt_after_login=prompt_after_login)

        self.timeout = 90
        # Parameters defined by calling the command
        self._re_failure_exceptions_indication = None
        if failure_exceptions_indication:
            self._re_failure_exceptions_indication = CommandTextualGeneric._calculate_prompt(
                failure_exceptions_indication)
        self.login = login
        if isinstance(password, six.string_types):
            self._passwords = [password]
        elif password is None:
            self._passwords = []
        else:
            self._passwords = copy_list(password, deep_copy=False)  # copy of list of passwords to modify
        self.host = host
        self.port = port
        self.term_mono = term_mono
        self.encrypt_password = encrypt_password
        self.repeat_password = repeat_password
        self.send_enter_after_connection = send_enter_after_connection

        # Internal variables
        self._sent_login = False
        self._last_password = ""

        if login and username:
            self.command_string = self.__class__.__name__
            raise CommandFailure(self, "Please set login ('{}') or username ('{}') but not both.".format(login,
                                                                                                         username))
        elif username:
            self.login = username
        self.current_ret['LINES'] = list()
        self.current_ret['LAST_LOGIN'] = dict()
        self.current_ret['FAILED_LOGIN_ATTEMPTS'] = None
        self._converter_helper = ConverterHelper.get_converter_helper()

    def on_new_line(self, line, is_full_line):
        """
        Parses the output of the command.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: None
        :raises: ParsingDone if any line matched the regex.
        """
        try:
            if is_full_line:
                self._add_line_to_ret(line)
            self._parse_failure_indication(line)
            self._send_login_if_requested(line)
            self._send_password_if_requested(line)
            self._just_connected(line)
        except ParsingDone:
            pass
        super(GenericTelnetSsh, self).on_new_line(line=line, is_full_line=is_full_line)

    # Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1
    _re_last_login = re.compile(r"Last login:\s+(?P<DATE>.*?)\s+(?P<KIND>from|on)\s+(?P<WHERE>\S+)", re.IGNORECASE)

    # There were 2 failed login attempts since the last successful login
    _re_attempts = re.compile(
        r'There (?:were|was|have been) (?P<ATTEMPTS_NR>\d+) (?:failed|unsuccessful) login attempts? '
        r'since the last successful login', re.I)

    def _add_line_to_ret(self, line):
        """
        Adds lint to ret value of command.

        :param line: line form connection.
        :return: None
        """
        self.current_ret['LINES'].append(line)
        if self._regex_helper.search_compiled(GenericTelnetSsh._re_last_login, line):
            date_raw = self._regex_helper.group("DATE")
            self.current_ret['LAST_LOGIN']['RAW_DATE'] = date_raw
            self.current_ret['LAST_LOGIN']['KIND'] = self._regex_helper.group("KIND")
            self.current_ret['LAST_LOGIN']['WHERE'] = self._regex_helper.group("WHERE")
            try:
                self.current_ret['LAST_LOGIN']['DATE'] = parser.parse(date_raw)
            except Exception:  # do not fail ssh or telnet if unknown date format.
                pass
        elif self._regex_helper.search_compiled(GenericTelnetSsh._re_attempts, line):
            self.current_ret['FAILED_LOGIN_ATTEMPTS'] = self._converter_helper.to_number(
                self._regex_helper.group("ATTEMPTS_NR"))

    def _parse_failure_indication(self, line):
        """
        Detects fail from command output.

        :param line: Line from device.
        :return: None.
        :raises: ParsingDone if line matched failure indication.
        """
        if self.is_failure_indication(line):
            if not self._is_failure_exception(line):
                self.set_exception(CommandFailure(self, "command failed in line '{}'".format(line)))
                raise ParsingDone()

    def _just_connected(self, line):
        """
        Checks if line contains has just connected.

        :param line: Line from device.
        :return: None but raises ParsingDone if line has information to handle by this method.
        """
        if self.send_enter_after_connection:
            if self._regex_helper.search_compiled(GenericTelnetSsh._re_has_just_connected, line):
                self.connection.send(self.target_newline)
                raise ParsingDone()

    def _send_login_if_requested(self, line):
        """
        Sends login if requested by server.

        :param line: Line from device.
        :return: None but raises ParsingDone if login was sent.
        """
        if (not self._sent_login) and self._is_login_requested(line) and self.login:
            self.connection.send("{}{}".format(self.login, self.target_newline))
            self._sent_login = True
            self._sent = False
            raise ParsingDone()

    def _send_password_if_requested(self, line):
        """
        Sends server if requested by server.

        :param line: Line from device.
        :return: None but raises ParsingDone if password was sent.
        """
        if (not self._sent) and self._is_password_requested(line):
            try:
                pwd = self._passwords.pop(0)
                self._last_password = pwd
                self.connection.send("{}{}".format(pwd, self.target_newline), encrypt=self.encrypt_password)
            except IndexError:
                if self.repeat_password:
                    self.connection.send("{}{}".format(self._last_password, self.target_newline),
                                         encrypt=self.encrypt_password)
                else:
                    self.set_exception(CommandFailure(self, "Password was requested but no more passwords provided."))
                    self.break_cmd()
            self._sent_login = False
            self._sent = True
            raise ParsingDone()

    def is_failure_indication(self, line):
        """
        Checks if line contains information that command fails.

        :param line: Line from device
        :return: Match object or None
        """
        return self._regex_helper.search_compiled(GenericTelnetSsh._re_failed_strings, line)

    def _is_failure_exception(self, line):
        """
        Checks if line contains exception information that command fails.

        :param line: Line from device
        :return: Match object or None
        """
        if not self._re_failure_exceptions_indication:
            return None
        return self._regex_helper.search_compiled(self._re_failure_exceptions_indication, line)

    def _is_login_requested(self, line):
        """
        Checks if line contains information that commands waits for login.

        :param line: Line from device
        :return: Match object or None
        """
        return self._regex_helper.search_compiled(GenericTelnetSsh._re_login, line)

    def _is_password_requested(self, line):
        """
        Checks if line contains information that commands waits for password.

        :param line: Line from device
        :return: Match object or None
        """
        return self._regex_helper.search_compiled(GenericTelnetSsh._re_password, line)
