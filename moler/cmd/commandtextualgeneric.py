# -*- coding: utf-8 -*-
"""
Generic Unix/Linux module
"""

__author__ = 'Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'marcin.usielski@nokia.com, michal.ernst@nokia.com'

import abc
import logging
import re

import six

from moler.cmd import RegexHelper
from moler.command import Command
from threading import Lock


@six.add_metaclass(abc.ABCMeta)
class CommandTextualGeneric(Command):
    """Base class for textual commands."""

    _re_default_prompt = re.compile(r'^[^<]*[\$|%|#|>|~]\s*$')  # When user provides no prompt
    _default_newline_chars = ("\n", "\r")  # New line chars on device, not system with script!

    def __init__(self, connection, prompt=None, newline_chars=None, runner=None):
        """
        Base class for textual commands.

        :param connection: connection to device.
        :param prompt: expected prompt sending by device after command execution. Maybe String or compiled re.
        :param newline_chars:  new line chars on device (a list).
        :param runner: runner to run command.
        """
        self._command_string_right_index = 20  # Right index of substring of command_string passed as _cmd_escaped. Set
        # 0 to disable functionality of substring.
        self.__command_string = None  # String representing command on device
        self._cmd_escaped = None  # Escaped regular expression string with command
        super(CommandTextualGeneric, self).__init__(connection=connection, runner=runner)
        self.terminating_timeout = 3.0  # value for terminating command if it timeouts. Set positive value for command
        #                                 if they can do anything if timeout. Set 0 for command if it cannot do
        #                                 anything if timeout.
        self.current_ret = dict()  # Placeholder for result as-it-grows, before final write into self._result
        self._cmd_output_started = False  # If false parsing is not passed to command
        self._regex_helper = RegexHelper()  # Object to regular expression matching
        self.ret_required = True  # # Set False for commands not returning parsed result
        self.break_on_timeout = True  # If True then Ctrl+c on timeout
        self._last_not_full_line = None  # Part of line
        self._re_prompt = CommandTextualGeneric._calculate_prompt(prompt)  # Expected prompt on device
        self._newline_chars = newline_chars  # New line characters on device
        self.do_not_process_after_done = True  # Set True if you want to break processing data when command is done. If
        # False then on_new_line will be called after done if more lines are in the same data package.
        self.newline_after_command_string = True  # Set True if you want to send a new line char(s) after command
        # string (sendline from connection)- most cases. Set False if you want to sent command string without adding
        # new line char(s) - send from connection.
        self.wait_for_prompt_on_exception = True  # Set True to wait for command prompt on failure. Set False to cancel
        # command immediately on failure.
        self._concatenate_before_command_starts = True  # Set True to concatenate all strings from connection before
        # command starts, False to split lines on every new line char
        self._stored_exception = None  # Exception stored before it is passed to base class when command is done.
        self._lock_is_done = Lock()

        if not self._newline_chars:
            self._newline_chars = CommandTextualGeneric._default_newline_chars

    @property
    def command_string(self):
        """
        Getter for command_string.

        :return: String with command_string.
        """
        if not self.__command_string:
            self.__command_string = self.build_command_string()
            self._build_command_string_escaped()
        return self.__command_string

    @command_string.setter
    def command_string(self, command_string):
        """
        Setter for command_string.

        :param command_string: Stting with command to set.
        :return: None.
        """
        self.__command_string = command_string
        self._build_command_string_escaped()

    def _build_command_string_escaped(self):
        """
        Builds escaped command string for regular expression based on command_string property .

        :return: None
        """
        self._cmd_escaped = None
        if self.__command_string is not None:
            sub_command_string = self.__command_string
            if self._command_string_right_index != 0:
                sub_command_string = self.__command_string[:self._command_string_right_index]
            self._cmd_escaped = re.compile(re.escape(sub_command_string))

    @property
    def _is_done(self):
        return super(CommandTextualGeneric, self)._is_done

    @_is_done.setter
    def _is_done(self, value):
        with self._lock_is_done:
            if self._stored_exception:
                exception = self._stored_exception
                self._stored_exception = None
                super(CommandTextualGeneric, self)._set_exception_without_done(exception=exception)
            super(CommandTextualGeneric, self.__class__)._is_done.fset(self, value)

    @staticmethod
    def _calculate_prompt(prompt):
        if not prompt:
            prompt = CommandTextualGeneric._re_default_prompt
        if isinstance(prompt, six.string_types):
            prompt = re.compile(prompt)
        return prompt

    def has_endline_char(self, line):
        """
        Method to check if line has chars of new line at the right side.

        :param line: String to check.
        :return: True if any new line char was found, False otherwise.
        """
        if line.endswith(self._newline_chars):
            return True
        return False

    def data_received(self, data):
        """
        Called by framework when any data are sent by device.

        :param data: List of strings sent by device.
        :return: None.
        """
        lines = data.splitlines(True)
        for line in lines:
            if self._last_not_full_line is not None:
                line = "{}{}".format(self._last_not_full_line, line)
                self._last_not_full_line = None
            is_full_line = self.has_endline_char(line)
            if is_full_line:
                line = self._strip_new_lines_chars(line)
            else:
                self._last_not_full_line = line
            if self._cmd_output_started:
                decoded_line = self._decode_line(line=line)
                self.on_new_line(line=decoded_line, is_full_line=is_full_line)
            else:
                self._detect_start_of_cmd_output(line, is_full_line)
                if self._concatenate_before_command_starts and not self._cmd_output_started and is_full_line:
                    self._last_not_full_line = line
            if self.done() and self.do_not_process_after_done:
                break

    @abc.abstractmethod
    def build_command_string(self):
        """
        Returns string with command constructed with parameters of object.

        :return:  String with command.
        """
        pass

    def on_new_line(self, line, is_full_line):
        """
        Method to parse command output. Will be called after line with command echo.
        Write your own implementation but don't forget to call on_new_line from base class in most cases.

        :param line: Line to parse, new lines are trimmed
        :param is_full_line: True if new line character was removed from line, False otherwise
        :return: None
        """
        if self.is_end_of_cmd_output(line):
            if self._stored_exception:
                self._is_done = True
            elif (self.ret_required and self.has_any_result()) or not self.ret_required:
                if not self.done():
                    self.set_result(self.current_ret)
            else:
                self._log(lvl=logging.DEBUG,
                          msg="Found candidate for final prompt but current ret is None or empty, required not None nor empty.")

    def is_end_of_cmd_output(self, line):
        """
        Checks if end of command is reached.

        :param line: Line from device.
        :return:
        """
        if self._regex_helper.search_compiled(self._re_prompt, line):
            return True
        return False

    def _strip_new_lines_chars(self, line):
        """
        Removes new line char(s) from line.

        :param line: line from device.
        :return: line without new lines chars.
        """
        for char in self._newline_chars:
            line = line.rstrip(char)
        return line

    def _detect_start_of_cmd_output(self, line, is_full_line):
        """
        Checks if command stated.

        :param line: line to check if echo of command is sent by device.
        :param is_full_line: True if line ends with new line char, False otherwise.
        :return: None.
        """
        if (is_full_line and self.newline_after_command_string) or not self.newline_after_command_string:
            if self._regex_helper.search_compiled(self._cmd_escaped, line):
                self._cmd_output_started = True

    def break_cmd(self):
        """
        Send ctrl+c to device to break command execution.

        :return: None
        """
        self.connection.send("\x03")  # ctrl+c

    def cancel(self):
        """
        Called by framework to cancel the command.

        :return: False if already cancelled or already done, True otherwise.
        """
        self.break_cmd()
        return super(CommandTextualGeneric, self).cancel()

    def set_exception(self, exception):
        """
        Set exception object as failure for command object.

        :param exception: An exception object to set.
        :return: None.
        """
        if self.done() or not self.wait_for_prompt_on_exception:
            super(CommandTextualGeneric, self).set_exception(exception=exception)
        else:
            if self._stored_exception is None:
                self._log(logging.INFO,
                          "{}.{} has set exception {!r}".format(self.__class__.__module__, self, exception),
                          levels_to_go_up=2)
                self._stored_exception = exception
            else:
                self._log(logging.INFO,
                          "{}.{} tried set exception {!r} on already set exception {!r}".format(
                              self.__class__.__module__,
                              self, exception,
                              self._stored_exception),
                          levels_to_go_up=2)

    def on_timeout(self):
        """
        Callback called by framework when timeout occurs.

        :return: None.
        """
        if self.break_on_timeout:
            self.break_cmd()
        msg = ("Timeout when command_string='{}', _cmd_escaped='{}', _cmd_output_started='{}', ret_required='{}', "
               "break_on_timeout='{}', _last_not_full_line='{}', _re_prompt='{}', do_not_process_after_done='{}', "
               "newline_after_command_string='{}', wait_for_prompt_on_exception='{}', _stored_exception='{}', "
               "current_ret='{}', _newline_chars='{}', _concatenate_before_command_starts='{}', "
               "_command_string_right_index='{}'.").format(
            self.__command_string, self._cmd_escaped, self._cmd_output_started, self.ret_required,
            self.break_on_timeout, self._last_not_full_line, self._re_prompt, self.do_not_process_after_done,
            self.newline_after_command_string, self.wait_for_prompt_on_exception, self._stored_exception,
            self.current_ret, self._newline_chars, self._concatenate_before_command_starts,
            self._command_string_right_index)
        self._log(logging.DEBUG, msg, levels_to_go_up=2)

    def has_any_result(self):
        """
        Checks if any result was already set by command.

        :return: True if current_ret has collected any data. Otherwise False.
        """
        is_ret = False
        if self.current_ret:
            is_ret = True
        return is_ret

    def send_command(self):
        """
        Sends command string over connection.

        :return: None
        """
        if self.newline_after_command_string:
            self.connection.sendline(self.command_string)
        else:
            self.connection.send(self.command_string)

    def _decode_line(self, line):
        """
        Decodes line if necessary. Put here code to remove colors from terminal etc.

        :param line: line from device to decode.
        :return: decoded line.
        """
        return line
