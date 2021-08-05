# -*- coding: utf-8 -*-
"""
Generic class for all command with textual output.
"""

__author__ = 'Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018-2021, Nokia'
__email__ = 'marcin.usielski@nokia.com, michal.ernst@nokia.com'

import abc
import logging
import re

import six

from moler.cmd import RegexHelper
from moler.command import Command
from threading import Lock

r_default_prompt = r'^[^<]*[$%#>~]\s*$'  # When user provides no prompt


@six.add_metaclass(abc.ABCMeta)
class CommandTextualGeneric(Command):
    """Base class for textual commands."""

    _re_default_prompt = re.compile(r_default_prompt)  # When user provides no prompt
    _default_newline_chars = ("\n", "\r")  # New line chars on device, not system with script!

    def __init__(self, connection, prompt=None, newline_chars=None, runner=None):
        """
        Base class for textual commands.

        :param connection: connection to device.
        :param prompt: expected prompt sending by device after command execution. Maybe String or compiled re.
        :param newline_chars:  new line chars on device (a list).
        :param runner: runner to run command.
        """
        self.command_path = None  # path to command executable - allow non standard locations like /usr/local/bin/
        self._max_index_from_beginning = 20  # Right (from 0 to this) index of substring of command_string passed
        # as _cmd_escaped. Set 0 to disable functionality of substring.
        self._max_index_from_end = 20  # Left (from this to the end) index of substring of command_string passed
        # as _cmd_escaped. Set 0 to disable functionality of substring.
        self._multiline_cmd = False
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
        self._ignore_unicode_errors = True  # If True then UnicodeDecodeError will be logged not raised in data_received
        self._last_recv_time_data_read_from_connection = None  # Time moment when data was really received from
        # connection (not when was passed to command).  Time is given as datetime.datetime instance
        self._remove_ctrlc_chars_for_prompt = True  # after sending Ctrl-C response might be concatenated ^Cprompt
        # This flag removes "^C" from prompt before processing prompt against self._re_prompt
        self._break_exec_regex = None  # Regex if not None then command will call break_cmd when this regex is caught
        # in on_new_line. Do not set directly, use setter break_exec_regex.
        self.break_exec_only_full_line = True  # Set True to consider only full lines to match _break_exec_regex or
        # False to consider also chunks.

        if not self._newline_chars:
            self._newline_chars = CommandTextualGeneric._default_newline_chars

    @property
    def break_exec_regex(self):
        """
        Getter for break_exec_regex

        :return: Regex object or None
        """
        return self._break_exec_regex

    @break_exec_regex.setter
    def break_exec_regex(self, break_exec_regex):
        """
        Setterfor break_exec_regex
        :param break_exec_regex: String with regex, compiled regex object or None
        :return: None
        """
        if isinstance(break_exec_regex, six.string_types):
            break_exec_regex = re.compile(break_exec_regex)
        self._break_exec_regex = break_exec_regex

    @property
    def command_string(self):
        """
        Getter for command_string.

        :return: String with command_string.
        """
        if not self.__command_string or (self.command_path and not self.__command_string.startswith(self.command_path)):
            try:
                self.__command_string = "CANNOT BUILD COMMAND STRING"  # To avoid infinite recursion if
                # build_command_string raises an exception.
                command_string = self.build_command_string()
                if self.command_path:
                    self.__command_string = "{}{}".format(self.command_path, command_string)
                else:
                    self.__command_string = command_string
            finally:
                self._build_command_string_escaped()
        return self.__command_string

    @command_string.setter
    def command_string(self, command_string):
        """
        Setter for command_string.

        :param command_string: String with command to set.
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
            command_string_copy = self.__command_string
            if self._multiline_cmd:
                command_string_copy = re.sub('\n', '', self.__command_string)
            if self._max_index_from_beginning != 0 or self._max_index_from_end != 0:
                sub_command_string = self._build_command_string_slice(command_string_copy)
            else:
                sub_command_string = re.escape(command_string_copy)

            self._cmd_escaped = re.compile(sub_command_string)

    def _build_command_string_slice(self, command_string):
        """
        Builds slice of command string.

        :param command_string: command_string to slice.
        :return: String with regex with command slice.
        """
        sub_command_start_string = None
        sub_command_finish_string = None
        re_sub_command_string = None
        if self._max_index_from_beginning != 0:
            sub_command_start_string = re.escape(command_string[:self._max_index_from_beginning])
            re_sub_command_string = sub_command_start_string
        if self._max_index_from_end != 0:
            sub_command_finish_string = re.escape(command_string[-self._max_index_from_end:])
            re_sub_command_string = sub_command_finish_string
        if sub_command_finish_string and sub_command_start_string:
            re_sub_command_string = "{}|{}".format(sub_command_start_string, sub_command_finish_string)
        return re_sub_command_string

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
            if value and not self._is_done:
                self.on_done()
                if self._stored_exception or self.cancelled():
                    self.on_failure()
                else:
                    self.on_success()
            super(CommandTextualGeneric, self.__class__)._is_done.fset(self, value)

    @staticmethod
    def _calculate_prompt(prompt):
        """
        Calculates prompt as regex from passed prompt.
        :param prompt: Prompt as regex  in string or as compiled regex object.
        :return: Compiled regex object.
        """
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

    def data_received(self, data, recv_time):
        """
        Called by framework when any data are sent by device.

        :param data: List of strings sent by device.
        :param recv_time: time stamp with the moment when the data was read from connection.  Time is given as
         datatime.datetime instance.
        :return: None.
        """
        self._last_recv_time_data_read_from_connection = recv_time
        try:
            lines = data.splitlines(True)
            for current_chunk in lines:
                if self.__class__.__name__ == 'CmConnect':  # pragma: no cover
                    self.logger.debug("{} current_chunk = '{}'".format(self, current_chunk))
                line, is_full_line = self._update_from_cached_incomplete_line(current_chunk=current_chunk)
                if self._cmd_output_started:
                    self._process_line_from_command(line=line, current_chunk=current_chunk, is_full_line=is_full_line)
                else:
                    self._detect_start_of_cmd_output(self._decode_line(line=line), is_full_line)
                    self._cache_line_before_command_start(line=line, is_full_line=is_full_line)
                if self.done() and self.do_not_process_after_done:
                    if self.__class__.__name__ == 'CmConnect':  # pragma: no cover
                        self.logger.debug("{} is done".format(self))
                    break
        except UnicodeDecodeError as ex:
            if self._ignore_unicode_errors:
                self._log(lvl=logging.WARNING,
                          msg="Processing data from '{}' with unicode problem: '{}'.".format(self, ex))
            else:
                # log it just to catch that rare hanging thread issue
                self._log(lvl=logging.WARNING,
                          msg="Processing data from '{}' raised: '{}'.".format(self, ex))
                raise ex
        except Exception as ex:  # pragma: no cover # log it just to catch that rare hanging thread issue
            self._log(lvl=logging.WARNING,
                      msg="Processing data from '{}' raised: '{}'.".format(self, ex))
            raise ex
        finally:
            if self.__class__.__name__ == 'CmConnect':  # pragma: no cover
                self.logger.debug("{} exiting data processing of '{}'".format(self, data))

    def _process_line_from_command(self, current_chunk, line, is_full_line):
        """
        Processes line from command.

        :param current_chunk: Chunk of line sent by connection.
        :param line: Line of output (current_chunk plus previous chunks of this line - if any) without newline char(s).
        :param is_full_line: True if line had newline char(s). False otherwise.
        :return: None.
        """
        decoded_line = self._decode_line(line=line)
        if self.__class__.__name__ == 'CmConnect':  # pragma: no cover
            self.logger.debug("{} line = '{}', decoded_line = '{}', is_full_line={}".format(self, line, decoded_line, is_full_line))
        self.on_new_line(line=decoded_line, is_full_line=is_full_line)

    def _cache_line_before_command_start(self, line, is_full_line):
        """
        Stores output before command starts.

        :param line: Line from device.
        :param is_full_line: True if line had new line char at the end. False otherwise.
        :return: None.
        """
        if self._concatenate_before_command_starts and not self._cmd_output_started and is_full_line:
            self._last_not_full_line = line

    def _update_from_cached_incomplete_line(self, current_chunk):
        """
        Concatenates (if necessary) previous chunk(s) of line and current.

        :param current_chunk: line from connection (full line or incomplete one).
        :return: Concatenated (if necessary) line from connection without newline char(s). Flag: True if line had
         newline char(s), False otherwise.
        """
        line = current_chunk
        if self._last_not_full_line is not None:
            line = u"{}{}".format(self._last_not_full_line, line)
            self._last_not_full_line = None
        is_full_line = self.has_endline_char(line)
        if is_full_line:
            line = self._strip_new_lines_chars(line)
        else:
            self._last_not_full_line = line
        return line, is_full_line

    @abc.abstractmethod
    def build_command_string(self):
        """
        Returns string with command constructed with parameters of object.

        :return:  String with command.
        """

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
                          msg="Found candidate for final prompt but current ret is None or empty, required not None"
                              " nor empty.")
        else:
            self._break_exec_on_regex(line=line, is_full_line=is_full_line)

    def is_end_of_cmd_output(self, line):
        """
        Checks if end of command is reached.

        :param line: Line from device.
        :return: True if end of command is reached, False otherwise.
        """
        if self._regex_helper.search_compiled(self._re_prompt, line):
            return True
        # when command is broken via Ctrl-C then ^C may be appended to start of prompt
        # if prompt regexp requires "at start of line" via r'^' then such ^C concatenation will falsify prompt
        if self._remove_ctrlc_chars_for_prompt and (len(line) > 2) and line.startswith("^C"):
            non_ctrl_c_started_line = line[2:]
            if self._regex_helper.search_compiled(self._re_prompt, non_ctrl_c_started_line):
                return True
        return False

    def _strip_new_lines_chars(self, line):
        """
        Removes new line char(s) from line.

        :param line: line from device.
        :return: line without new lines chars.
        """
        if len(line) >= 1:
            last_char = line[-1]
            while last_char in self._newline_chars:
                line = line.rstrip(last_char)
                if len(line) >= 1:
                    last_char = line[-1]
                else:
                    last_char = None
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
        if self.__class__.__name__ == 'CmConnect':  # pragma: no cover
            self.logger.debug("{} line = '{}', is_full_line={}, _cmd_output_started={}".format(self, line, is_full_line, self._cmd_output_started))

    def break_cmd(self, silent=False):
        """
        Send ctrl+c to device to break command execution.

        :return: None
        """
        if self.running():
            self.connection.send("\x03")  # ctrl+c
        else:
            if silent is False:
                self._log(lvl=logging.WARNING, msg="Tried to break not running command '{}'. Ignored".format(self))

    def cancel(self):
        """
        Called by framework to cancel the command.

        :return: False if already cancelled or already done, True otherwise.
        """
        self.break_cmd(silent=True)
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

    def on_failure(self):
        """
        Callback called by framework when command is just about to finish with failure. Set ret is called.

        :return: None
        """

    def on_success(self):
        """
        Callback called by framework when command is just about to finish with success. Set ret is called.

        :return: None
        """

    def on_done(self):
        """
        Callback called by framework when command is just about to finish.

        :return: None
        """

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
               "_command_string_right_index='{}', _command_string_left_index='{}'.").format(
            self.__command_string, self._cmd_escaped.pattern, self._cmd_output_started, self.ret_required,
            self.break_on_timeout, self._last_not_full_line, self._re_prompt.pattern, self.do_not_process_after_done,
            self.newline_after_command_string, self.wait_for_prompt_on_exception, self._stored_exception,
            self.current_ret, self._newline_chars, self._concatenate_before_command_starts,
            self._max_index_from_beginning, self._max_index_from_end)
        self._log(lvl=logging.INFO, msg=msg, levels_to_go_up=2)

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

    def _break_exec_on_regex(self, line, is_full_line):
        """
        Breaks the execution of the command if self._break_exec_regex matches line.

        :param line: line from connection.
        :param is_full_line: True if new line character was removed from line, False otherwise
        :return: None
        """
        if self.break_exec_only_full_line and not is_full_line:
            return
        if self.break_exec_regex is not None and self._regex_helper.search_compiled(self.break_exec_regex, line):
            self.break_cmd()
