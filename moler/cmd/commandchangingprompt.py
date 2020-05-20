# -*- coding: utf-8 -*-
"""
Generic command class for commands change prompt
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2019-2020, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import abc
import six

from moler.cmd.commandtextualgeneric import CommandTextualGeneric
from moler.exceptions import ParsingDone


@six.add_metaclass(abc.ABCMeta)
class CommandChangingPrompt(CommandTextualGeneric):
    """Base class for textual commands to change prompt."""

    def __init__(self, connection, prompt, expected_prompt, newline_chars=None, runner=None,
                 set_timeout=None, set_prompt=None, target_newline="\n", allowed_newline_after_prompt=False,
                 prompt_after_login=None):
        """
        Moler base class for commands that change prompt.

        :param connection: moler connection to device, terminal when command is executed.
        :param prompt: prompt on start system (where command starts).
        :param expected_prompt: prompt on server (where command connects).
        :param newline_chars: characters to split lines.
        :param runner: Runner to run command.
        :param set_timeout: Command to set timeout after telnet connects.
        :param set_prompt: Command to set prompt after telnet connects.
        :param target_newline: newline chars on remote system where ssh connects.
        :param allowed_newline_after_prompt: If True then newline chars may occur after expected (target) prompt.
        :param prompt_after_login: prompt after login before send export PS1. If you do not change prompt exporting PS1
         then leave it None.
        """
        super(CommandChangingPrompt, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                                    runner=runner)

        # Parameters defined by calling the command
        self._re_expected_prompt = CommandTextualGeneric._calculate_prompt(expected_prompt)  # Expected prompt on device
        self._re_prompt_after_login = self._re_expected_prompt
        if prompt_after_login:
            self._re_prompt_after_login = CommandTextualGeneric._calculate_prompt(prompt_after_login)
        self.set_timeout = set_timeout
        self.set_prompt = set_prompt
        self.target_newline = target_newline
        self.allowed_newline_after_prompt = allowed_newline_after_prompt

        # Internal variables
        self._re_failure_exceptions_indication = None
        self._sent_timeout = False
        self._sent_prompt = False
        self._sent = False
        self._finish_on_final_prompt = True  # Set True to finish Moler command by this generic after prompt after
        # command output. False if you want to finish command in your class.

    def __str__(self):
        base_str = super(CommandChangingPrompt, self).__str__()
        expected_prompt = self._re_expected_prompt.pattern
        # having expected prompt visible simplifies troubleshooting
        return "{}, expected_prompt_regex:r'{}')".format(base_str[:-1], expected_prompt)

    def on_new_line(self, line, is_full_line):
        """
        Parses the output of the command.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: None
        """
        try:
            self._settings_after_login(line, is_full_line)
            self._detect_prompt_after_exception(line)
        except ParsingDone:
            pass
        if self._sent and is_full_line:
            self._sent = False

    def _detect_prompt_after_exception(self, line):
        """
        Detects start prompt.

        :param line: Line from device.
        :return: None but raises ParsingDone if detects start prompt and any exception was set.
        """
        if self._stored_exception and self._regex_helper.search_compiled(self._re_prompt, line):
            self._is_done = True
            raise ParsingDone()

    def _settings_after_login(self, line, is_full_line):
        """
        Checks if settings after login are requested and sent.

        :param line: Line from device.
        :param is_full_line: True if line had new line chars, False otherwise.
        :return: None but raises ParsingDone if line has information to handle by this method.
        """
        sent = self._send_after_login_settings(line)
        if sent:
            raise ParsingDone()
        if (not sent) and self._is_target_prompt(line) and (not is_full_line or self.allowed_newline_after_prompt):
            if self._all_after_login_settings_sent() or self._no_after_login_settings_needed():
                if not self.done() and self._cmd_output_started:
                    if self._finish_on_final_prompt:
                        self.set_result(self.current_ret)
                    raise ParsingDone()

    def _send_after_login_settings(self, line):
        """
        Sends commands to set timeout and to change prompt.

        :param line: Line from device.
        :return: True if any command was sent, False if no command was sent.
        """
        if self._is_prompt_after_login(line):
            if self._commands_to_set_connection_after_login(line):
                return True
            if self._timeout_set_needed() and not self._sent:
                self._send_timeout_set()
                return True  # just sent
            elif self._prompt_set_needed() and not self._sent:
                self._send_prompt_set()
                return True  # just sent
        return False  # nothing sent

    def _commands_to_set_connection_after_login(self, line):
        return False

    def _no_after_login_settings_needed(self):
        """
        Checks if prompt and timeout commands are sent.

        :return: True if commands for login nor timeout are no needed.
        """
        return (not self.set_prompt) and (not self.set_timeout)

    def _timeout_set_needed(self):
        """
        Checks if command to set timeout is still needed.

        :return: True if command to set timeout is needed, otherwise (sent or not requested) False
        """
        return self.set_timeout and not self._sent_timeout

    def _send_timeout_set(self):
        """
        Sends command to set timeout

        :return: None
        """
        self.connection.sendline("")
        self.connection.sendline(self.set_timeout)
        self._sent_timeout = True
        self._sent = True

    def _prompt_set_needed(self):
        """
        Checks if command to set prompt is still needed.

        :return: True if command to set prompt is needed, otherwise (sent or not requested) False
        """
        return self.set_prompt and not self._sent_prompt

    def _send_prompt_set(self):
        """
        Sends command to set prompt.

        :return: None
        """
        self.connection.sendline("")
        self.connection.sendline(self.set_prompt)
        self._sent_prompt = True
        self._sent = True

    def _is_target_prompt(self, line):
        """
        Checks if line contains prompt on target system.

        :param line: Line from device
        :return: Match object or None
        """
        found = self._regex_helper.search_compiled(self._re_expected_prompt, line)
        return found

    def _is_prompt_after_login(self, line):
        """
        Checks if line contains prompt just after login.

        :param line: Line from device
        :return: Match object or None
        """
        found = self._regex_helper.search_compiled(self._re_prompt_after_login, line)
        return found

    def _all_after_login_settings_sent(self):
        """
        Checks if all commands were sent by telnet command.

        :return: True if all requested commands were sent, False if at least one left.
        """
        additional_commands_sent = self._sent_additional_settings_commands()  # Useful for Telnet commands
        both_requested = self.set_prompt and self.set_timeout
        both_sent = self._sent_prompt and self._sent_timeout
        req_and_sent_prompt = self.set_prompt and self._sent_prompt
        req_and_sent_timeout = self.set_timeout and self._sent_timeout
        terminal_cmds_sent = ((both_requested and both_sent) or req_and_sent_timeout or req_and_sent_prompt)
        return terminal_cmds_sent and additional_commands_sent

    def _sent_additional_settings_commands(self):
        """
        Checks if additional commands after connection established are sent (useful for telnet, not used for ssh).

        :return: True if all additional commands are sent (if any). False if any command left in the queue.
        """
        return True

    @abc.abstractmethod
    def build_command_string(self):
        """
        Returns string with command constructed with parameters of object.

        :return:  String with command.
        """
