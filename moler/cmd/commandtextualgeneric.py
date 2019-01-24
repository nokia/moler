# -*- coding: utf-8 -*-
"""
Generic Unix/Linux module
"""

__author__ = 'Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com, michal.ernst@nokia.com'

import abc
import logging
import re

import six

from moler.cmd import RegexHelper
from moler.command import Command


class CommandTextualGeneric(Command):
    _re_default_prompt = re.compile(r'^[^<]*[\$|%|#|>|~]\s*$')  # When user provides no prompt
    _default_newline_chars = ("\n", "\r")  # New line chars on device, not system with script!

    def __init__(self, connection, prompt=None, newline_chars=None, runner=None):
        """
        :param connection: connection to device
        :param prompt: expected prompt sending by device after command execution. Maybe String or compiled re
        :param newline_chars:  new line chars on device
        """
        super(CommandTextualGeneric, self).__init__(connection=connection, runner=runner)
        self.__command_string = None  # String representing command on device
        self.current_ret = dict()  # Placeholder for result as-it-grows, before final write into self._result
        self._cmd_escaped = None  # Escaped regular expression string with command
        self._cmd_output_started = False  # If false parsing is not passed to command
        self._regex_helper = RegexHelper()  # Object to regular expression matching
        self.ret_required = True  # # Set False for commands not returning parsed result
        self.break_on_timeout = True  # If True then Ctrl+c on timeout
        self._last_not_full_line = None  # Part of line
        self._re_prompt = CommandTextualGeneric._calculate_prompt(prompt)  # Expected prompt on device
        self._newline_chars = newline_chars  # New line characters on device
        self.do_not_process_after_done = True  # Set True if you want to break processing data when command is done. If
        # False then on_new_line will be called after done if more lines are in the same data package.

        if not self._newline_chars:
            self._newline_chars = CommandTextualGeneric._default_newline_chars

    @property
    def command_string(self):
        if not self.__command_string:
            self.__command_string = self.build_command_string()
            self._cmd_escaped = re.escape(self.__command_string)
        return self.__command_string

    @command_string.setter
    def command_string(self, command_string):
        self.__command_string = command_string
        self._cmd_escaped = re.escape(command_string)

    @staticmethod
    def _calculate_prompt(prompt):
        if not prompt:
            prompt = CommandTextualGeneric._re_default_prompt
        if isinstance(prompt, six.string_types):
            prompt = re.compile(prompt)
        return prompt

    def has_endline_char(self, line):
        """
        Method to check if line has chars of new line at the right side
        :param line: String to check
        :return: True if any new line char was found, False otherwise
        """
        if line.endswith(self._newline_chars):
            return True
        return False

    def data_received(self, data):
        """
        Called by framework when any data are sent by device
        :param data: List of strings sent by device
        :return: Nothing
        """
        lines = data.splitlines(True)
        for line in lines:
            if self._last_not_full_line is not None:
                line = self._last_not_full_line + line
                self._last_not_full_line = None
            is_full_line = self.has_endline_char(line)
            if is_full_line:
                line = self._strip_new_lines_chars(line)
            else:
                self._last_not_full_line = line
            if self._cmd_output_started:
                self.on_new_line(line, is_full_line)
            elif is_full_line:
                self._detect_start_of_cmd_output(line)
            if self.done() and self.do_not_process_after_done:
                break

    @abc.abstractmethod
    def build_command_string(self):
        """
        :return:  String with command
        """
        pass

    def on_new_line(self, line, is_full_line):
        """
        Method to parse command output. Will be called after line with command echo.
        Write your own implementation but don't forget to call on_new_line from base class
        :param line: Line to parse, new lines are trimmed
        :param is_full_line: True if new line character was removed from line, False otherwise
        :return: Nothing
        """
        if self.is_end_of_cmd_output(line):
            if (self.ret_required and self.has_any_result()) or not self.ret_required:
                if not self.done():
                    self.set_result(self.current_ret)
            else:
                self._log(lvl=logging.DEBUG,
                          msg="Found candidate for final prompt but current ret is None or empty, required not None nor empty.")

    def is_end_of_cmd_output(self, line):
        if self._regex_helper.search_compiled(self._re_prompt, line):
            return True
        return False

    def _strip_new_lines_chars(self, line):
        """
        :param line: line from device
        :return: line without new lines chars
        """
        for char in self._newline_chars:
            line = line.rstrip(char)
        return line

    def _detect_start_of_cmd_output(self, line):
        """
        :param line: line to check if echo of command is sent by device
        :return: Nothing
        """
        if self._regex_helper.search(self._cmd_escaped, line):
            self._cmd_output_started = True

    def break_cmd(self):
        """
        Send ctrl+c to device to break command execution
        :return:
        """
        self.connection.send("\x03")  # ctrl+c

    def cancel(self):
        """
        Called by framework to cancel the command
        :return:
        """
        self.break_cmd()
        return super(CommandTextualGeneric, self).cancel()

    def on_timeout(self):
        """
        Callback called by framework when timeout occurs
        :return: Nothing
        """
        if self.break_on_timeout:
            self.break_cmd()

    def has_any_result(self):
        """
        :return: True if current_ret has collected any data. Otherwise False
        """
        is_ret = False
        if self.current_ret:
            is_ret = True
        return is_ret
