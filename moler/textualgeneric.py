# -*- coding: utf-8 -*-
"""
Generic Unix/Linux module
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import abc
import logging
import re
import sys

from moler.cmd import RegexHelper
from moler.command import Command


class TextualGeneric(Command):
    _re_default_prompt = re.compile(r'^[^<]*[\$|%|#|>|~]\s*$')  # When user provides no prompt
    _default_new_line_chars = ("\n", "\r")  # New line chars on device, not system with script!
    _re_color_codes = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")  # Regex to remove color codes from command output

    def __init__(self, connection, prompt=None, new_line_chars=None):
        """
        :param connection: connection to device
        :param prompt: expected prompt sending by device after command execution. Maybe String or compiled re
        :param new_line_chars:  new line chars on device
        """
        super(TextualGeneric, self).__init__(connection)
        self.logger = logging.getLogger('moler.conn-observer')
        self.__command_string = None  # String representing command on device
        self.current_ret = dict()  # Placeholder for result as-it-grows, before final write into self._result
        self._cmd_escaped = None  # Escaped regular expression string with command
        self._cmd_output_started = False  # If false parsing is not passed to command
        self._regex_helper = RegexHelper()  # Object to regular expression matching
        self.ret_required = True  # # Set False for commands not returning parsed result
        self.break_on_timeout = True  # If True then Ctrl+c on timeout
        self._last_not_full_line = None  # Part of line
        self._re_prompt = TextualGeneric._calculate_prompt(prompt)  # Expected prompt on device
        self._new_line_chars = new_line_chars  # New line characters on device
        self.remove_colors_from_terminal_output = True
        if not self._new_line_chars:
            self._new_line_chars = TextualGeneric._default_new_line_chars

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
            prompt = TextualGeneric._re_default_prompt
        if sys.version_info >= (3, 0):
            if isinstance(prompt, str):
                prompt = re.compile(prompt)
        else:
            if isinstance(prompt, basestring):
                prompt = re.compile(prompt)
        return prompt

    def is_new_line(self, line):  # TODO: change to has_endline_char()
        """
        Method to check if line has chars of new line at the right side
        :param line: String to check
        :return: True if any new line char was found, False otherwise
        """
        if line.endswith(self._new_line_chars):
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
            is_full_line = self.is_new_line(line)
            if is_full_line:
                line = self._strip_new_lines_chars(line)
                if self.remove_colors_from_terminal_output:
                    line = self._remove_color_terminal_codes(line)
            else:
                self._last_not_full_line = line
            if self._cmd_output_started:
                self.on_new_line(line, is_full_line)
            elif is_full_line:
                self._detect_start_of_cmd_output(line)

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
                self.logger.debug(
                    "Found candidate for final prompt but current ret is None or empty, required not None nor empty.")

    def is_end_of_cmd_output(self, line):
        if self._regex_helper.search_compiled(self._re_prompt, line):
            return True
        return False

    def _strip_new_lines_chars(self, line):
        """
        :param line: line from device
        :return: line without new lines chars
        """
        for char in self._new_line_chars:
            line = line.rstrip(char)
        return line

    def _remove_color_terminal_codes(self, line):
        """
        :param line: line from terminal
        :return: line without terminal color codes
        """
        line = re.sub(TextualGeneric._re_color_codes, "", line)
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
        return super(TextualGeneric, self).cancel()

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
