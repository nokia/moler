# -*- coding: utf-8 -*-
"""
Generic Unix/Linux module
"""
import re
import abc
import sys

from moler.cmd import RegexHelper
from moler.command import Command

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'


class TextualGeneric(Command):

    _re_default_prompt = re.compile(r'^[^<]*[\$|%|#|>|~]\s*$')  # When user doesn't provide anything
    _default_new_line_chars = ("\n", "\r")  # New line chars on device, not system with script!

    def __init__(self, connection, prompt=None, new_line_chars=None):
        """
        :param connection: connection to device
        :param prompt: expected prompt sending by device after command execution. Maybe String or compiled re
        :param new_line_chars:  new line chars on device
        """
        super(TextualGeneric, self).__init__(connection)
        self.__command_string = None  # String representing command on device
        self.current_ret = dict()  # Store everything here for user
        self._cmd_escaped = None  # Escaped regular expression string with command
        self._cmd_matched = False  # If false parsing is not passed to command
        self._regex_helper = RegexHelper()  # Object to regular expression matching
        self.ret_required = True  # Set true if something must be parsed
        self.break_on_timeout = True  # If True then Ctrl+c on timeout
        self._last_not_full_line = None  # Part of line
        self._reg_prompt = prompt  # Expected prompt on device
        if not self._reg_prompt:
            self._reg_prompt = TextualGeneric._re_default_prompt
        if sys.version_info >= (3, 0):
            if isinstance(self._reg_prompt, str):
                self._reg_prompt = re.compile(self._reg_prompt)
        else:
            if isinstance(self._reg_prompt, basestring):
                self._reg_prompt = re.compile(self._reg_prompt)
        self._new_line_chars = new_line_chars  # New line characters on device
        if not self._new_line_chars:
            self._new_line_chars = TextualGeneric._default_new_line_chars

    @property
    def command_string(self):
        if not self.__command_string:
            self.__command_string = self.get_cmd()
            self._cmd_escaped = re.escape(self.__command_string)
        return self.__command_string

    @command_string.setter
    def command_string(self, command_string):
        self.__command_string = command_string
        self._cmd_escaped = re.escape(command_string)

    def is_new_line(self, line):
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
            if self._cmd_matched:
                is_full_line = self.is_new_line(line)
                if is_full_line:
                    for char in self._new_line_chars:
                        line = line.rstrip(char)
                self.on_new_line(line, is_full_line)
            elif self._regex_helper.search(self._cmd_escaped, line) and self.is_new_line(line):
                self._cmd_matched = True

    @abc.abstractmethod
    def get_cmd(self, cmd=None):
        """
        :param cmd:  If provided then parameters form command will not be used
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
        if self._regex_helper.search_compiled(self._reg_prompt, line):
            if (self.ret_required and self.is_ret()) or not self.ret_required:
                if not self.done():
                    self.set_result(self.current_ret)
                else:
                    # print("Found candidate for final prompt but current ret is None or empty, required not None nor empty.")
                    pass

    def has_cmd_run(self):
        """
        :return: True if command string was already parsed in output. False otherwise
        """
        return self._cmd_matched

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

    def timeout(self):
        """
        Called by framework when timeout occurs
        :return: Nothing
        """
        if self.break_on_timeout:
            self.break_cmd()

    def is_ret(self):
        """
        :return: True if current_ret has anything. Otherwise False.
        """
        is_ret = False
        if self.current_ret:
            is_ret = True
        return is_ret
