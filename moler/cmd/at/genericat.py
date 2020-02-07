# -*- coding: utf-8 -*-
"""
Common part for all commands.

AT commands specification:
google for: 3gpp specification 27.007
(always check against latest version of standard)
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import re
import abc
import six
from moler.cmd.commandtextualgeneric import CommandTextualGeneric
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone


class AtCommandModeNotSupported(Exception):
    pass


class AtCommandFailure(CommandFailure):
    pass


@six.add_metaclass(abc.ABCMeta)
class GenericAtCommand(CommandTextualGeneric):
    _re_default_at_prompt = re.compile(r'^\s*(OK|ERROR|\+CM[ES]\s+ERROR:\s*\S.+)\s*$')  # When user provides no prompt

    def __init__(self, connection, operation="execute", prompt=None, newline_chars=None, runner=None):
        """
        Create instance of At class - base class for all AT commands

        :param connection: connection used to send command and receive its output
        :param operation: "execute", "read", "test" (not all AT commands support all modes)
        :param prompt: prompt (on system where command runs).
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        """
        if operation not in ["execute", "read", "test"]:
            raise AtCommandModeNotSupported("{} mode not supported for command {}".format(operation,
                                                                                          self.__class__.__name__))
        if prompt is None:
            prompt = self._re_default_at_prompt
        self.operation = operation
        self._at_command_base_string = ""
        self._at_command_execute_params = ""
        super(GenericAtCommand, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                               runner=runner)
        # TODO: do we have any way to stop AT cmd?
        self.terminating_timeout = 0  # no additional timeout for Ctrl-C..till..prompt (shutdown after cmd timeout)

    def on_new_line(self, line, is_full_line):
        """
        Method to parse command output. Will be called after line with command echo.
        Write your own implementation but don't forget to call on_new_line from base class

        :param line: Line to parse, new lines are trimmed
        :param is_full_line:  False for chunk of line; True on full line (NOTE: new line character removed)
        :return: None
        """
        if is_full_line:
            try:
                self._parse_error_response(line)
            except ParsingDone:
                pass
        return super(GenericAtCommand, self).on_new_line(line, is_full_line)

    def _is_at_cmd_echo(self, line):
        return self._regex_helper.search_compiled(self._cmd_escaped, line)

    _re_success = re.compile(r"^\s*OK\s*$")

    def _is_at_cmd_success(self, line):
        match = self._regex_helper.match_compiled(self._re_success, line)
        return match is not None

    _re_error = re.compile(r'^\s*ERROR\s*$')
    _re_cme_error = re.compile(r'^\+(?P<ERR_TYPE>CM[ES])\s+ERROR:\s*(?P<ERROR>\S.+)', flags=re.IGNORECASE)

    def _parse_error_response(self, line):
        """
        When command itself is invalid or cannot be performed for some reason,
        or mobile termination error reporting is disabled:
        at+cmd
        ERROR

        When command was not processed due to an error related to MT operation:
        at+cmd
        +CME ERROR: result code

        See https://www.smssolutions.net/tutorials/gsm/gsmerrorcodes/
        """
        if self._regex_helper.match_compiled(self._re_cme_error, line):
            error_type = self._regex_helper.group("ERR_TYPE")
            error_info = self._regex_helper.group("ERROR")
            self.set_exception(AtCommandFailure(self, "{} ERROR: {}".format(error_type, error_info)))
            raise ParsingDone
        elif self._regex_helper.match_compiled(self._re_error, line):
            self.set_exception(AtCommandFailure(self, "ERROR"))
            raise ParsingDone

    def set_at_command_string(self, command_base_string, execute_params=None):  # TODO: *execute_params as pairs list
        """
        Build full command-string of AT-cmd

        :param command_base_string: what AT command we run
        :param execute_params: list of (param, value) for operation 'execute'. Need list - order is important.
        :return: None
        """
        self._at_command_base_string = command_base_string
        if execute_params:
            params = ",".join(str(param_value) for param_name, param_value in execute_params if param_value or (param_value == 0))
            # param_value == 0  may generate valid AT-cmd like:
            # AT+CBST=0,0,0
            self._at_command_execute_params = params

    def build_command_string(self):
        """
        Returns string with command constructed with parameters of object.

        :return:  String with command.
        """
        assert self._at_command_base_string, "You should call set_at_command_string()"
        if self.operation == 'test':
            cmd = "{}=?".format(self._at_command_base_string)
        elif self.operation == "read":
            cmd = "{}?".format(self._at_command_base_string)
        elif self._at_command_execute_params:  # operation == "execute" with params
            cmd = "{}={}".format(self._at_command_base_string, self._at_command_execute_params)
        else:  # operation == "execute" without params
            cmd = self._at_command_base_string
        return cmd
