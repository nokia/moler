# -*- coding: utf-8 -*-
"""
Generic command class for commands change prompt
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2019-2024, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import abc
import six
import re

from moler.cmd.commandtextualgeneric import CommandTextualGeneric
from moler.exceptions import ParsingDone
from moler.helpers import regexp_without_anchors


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
        self.enter_on_prompt_without_anchors = True  # Set True to try to match prompt in line without ^ and $.
        self.check_echo_settings = True  # Set True to check if echo of commands to set prompt and timeout is matched.

        # Internal variables
        self._re_failure_exceptions_indication = None
        # self._sent_timeout = False
        # self._sent_prompt = False
        # self._matched_timeout = False
        # self._matched_prompt = False
        self._sent = False
        self._finish_on_final_prompt = True  # Set True to finish Moler command by this generic after prompt after
        # command output. False if you want to finish command in your class.

        self._re_expected_prompt_without_anchors = regexp_without_anchors(self._re_expected_prompt)
        self._re_prompt_after_login_without_anchors = regexp_without_anchors(self._re_prompt_after_login)
        self._re_timeout_echo = None
        self._re_prompt_echo = None
        if self.set_timeout:
            self._re_timeout_echo = re.compile(self._build_command_string_slice(self.set_timeout))
        if self.set_prompt:
            self._re_prompt_echo = re.compile(self._build_command_string_slice(self.set_prompt))
        self._commands_to_send_when_prompt = []
        self._commands_to_send_when_after_login_prompt = []
        if self.set_timeout:
            self._commands_to_send_when_after_login_prompt.append(self.set_timeout)
        if self.set_prompt:
            self._commands_to_send_when_after_login_prompt.append(self.set_prompt)
        self._commands_to_send_when_expected_prompt = []
        self._sent = False

    def __str__(self):
        """
        Return a string representation of the CommandChangingPrompt object.

        The string representation includes the base string representation
        obtained from the superclass, as well as the regular expressions
        for the expected prompt and the prompt after login.

        :return: A string representation of the CommandChangingPrompt object.
        """
        base_str = super(CommandChangingPrompt, self).__str__()
        expected_prompt = self._re_expected_prompt.pattern
        prompt_after_login = self._re_prompt_after_login.pattern
        # having expected prompt visible simplifies troubleshooting
        return f"{base_str[:-1]}, expected_prompt_regex:r'{expected_prompt}', prompt_after_login:r'{prompt_after_login}')"

    def on_new_line(self, line: str, is_full_line: bool) -> None:
        """
        Parses the output of the command.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: None
        """
        try:
            self._detect_prompts_without_anchors(line, is_full_line)
            self._detect_final_prompt(line, is_full_line)
            self._detect_prompt_after_exception(line)
            self._send_commands_when_prompt(line)
            self._send_commands_when_after_login_prompt(line)
            self._send_commands_when_expected_prompt(line)
        except ParsingDone:
            pass
        if is_full_line:
            self._sent = False

    def _detect_prompts_without_anchors(self, line: str, is_full_line: bool):
        if is_full_line or not self.enter_on_prompt_without_anchors or self._sent:
            return
        msg = None
        if self._is_prompt_without_anchors(line=line, prompt_without_anchors=self._re_prompt_after_login_without_anchors,
                                           prompt=self._re_prompt_after_login):
            msg = f"Candidate for prompt after login '{self._re_prompt_after_login.pattern}' " \
                  f"(used without anchors:'{self._re_prompt_after_login_without_anchors.pattern}') " \
                  f"in line '{line}'."
        elif self._is_prompt_without_anchors(line=line, prompt_without_anchors=self._re_expected_prompt_without_anchors,
                                           prompt=self._re_expected_prompt):
            msg = f"Candidate for prompt after login '{self._re_expected_prompt.pattern}' " \
                  f"(used without anchors:'{self._re_expected_prompt_without_anchors.pattern}') " \
                  f"in line '{line}'."
        if msg:
            self.logger.info(msg)
            raise ParsingDone()

    def _is_prompt_without_anchors(self, line: str, prompt_without_anchors, prompt) -> bool:
        found = self._regex_helper.search_compiled(prompt, line)
        if not found:
            if self._regex_helper.search_compiled(
                    prompt_without_anchors, line):
                self._sent = True
                self.send_enter()
                return True
        return False

    def _send_commands_when_prompt(self, line: str) -> None:
        """
        Sends commands when start prompt is detected.

        :param line: Line from device.
        :return: None
        """
        self._parse_prompt_and_send_command(line=line, prompt=self._re_prompt,
                                            commands=self._commands_to_send_when_prompt)

    def _send_commands_when_after_login_prompt(self, line: str) -> None:
        """
        Sends commands when after login prompt is detected.

        :param line: Line from device.
        :return: None
        """
        self._parse_prompt_and_send_command(line=line, prompt=self._re_prompt_after_login,
                                            commands=self._commands_to_send_when_after_login_prompt)

    def _send_commands_when_expected_prompt(self, line: str) -> None:
        """
        Sends commands when final prompt is detected.

        :param line: Line from device.
        :return: None
        """
        self._parse_prompt_and_send_command(line=line, prompt=self._re_expected_prompt,
                                            commands=self._commands_to_send_when_expected_prompt)

    def _parse_prompt_and_send_command(self, line: str, prompt, commands: list) -> None:
        if self._sent:
            return
        if len(commands) > 0 and self._regex_helper.search_compiled(prompt, line):
            cmd = commands.pop(0)
            self._sent = True
            self.connection.sendline(cmd)
            raise ParsingDone()

    def _detect_final_prompt(self, line: str, is_full_line: bool) -> None:
        if self._is_target_prompt(line) and (not is_full_line or self.allowed_newline_after_prompt):
            if self._sent is False and self._are_settings_needed() is False:
                if not self.done() and self._cmd_output_started:
                    if self._finish_on_final_prompt:
                        self.set_result(self.current_ret)
                    raise ParsingDone()

    def _are_settings_needed(self) -> bool:
        if (len(self._commands_to_send_when_expected_prompt) > 0 or
                len(self._commands_to_send_when_after_login_prompt) > 0):
            return True
        return False

    def _detect_prompt_after_exception(self, line: str):
        """
        Detects start prompt.

        :param line: Line from device.
        :return: None but raises ParsingDone if detects start prompt and any exception
         was set.
        """
        if self._stored_exception and self._regex_helper.search_compiled(self._re_prompt, line):
            self._is_done = True
            raise ParsingDone()

    def _is_target_prompt(self, line: str) -> bool:
        """
        Checks if line contains prompt on target system.

        :param line: Line from device
        :return: True if line contains prompt on target device, False otherwise
        """
        found = self._regex_helper.search_compiled(self._re_expected_prompt, line)
        return found is not None

    def _is_prompt_after_login(self, line: str) -> bool:
        """
        Checks if line contains prompt just after login.

        :param line: Line from device
        :return: True if line contains prompt just after login. False otherwise.
        """
        found = self._regex_helper.search_compiled(self._re_prompt_after_login, line)
        if not found and self.enter_on_prompt_without_anchors is True:
            if self._regex_helper.search_compiled(self._re_prompt_after_login_without_anchors, line):
                msg = f"Candidate for prompt after login '{self._re_prompt_after_login.pattern}' in line '{line}'."
                self.logger.info(msg)
                self.send_enter()
                self.enter_on_prompt_without_anchors = False
        return found is not None

    # def _all_after_login_settings_sent(self) -> bool:
    #     """
    #     Checks if all commands were sent by telnet command.
    #
    #     :return: True if all requested commands were sent, False if at least one left.
    #     """
    #     additional_commands_sent = self._sent_additional_settings_commands()  # Useful for Telnet commands
    #     both_requested = self.set_prompt and self.set_timeout
    #     both_sent = self._sent_prompt and self._sent_timeout
    #     req_and_sent_prompt = self.set_prompt and self._sent_prompt
    #     req_and_sent_timeout = self.set_timeout and self._sent_timeout
    #     if self.check_echo_settings:
    #         if both_sent:
    #             both_sent = both_sent and self._matched_prompt and self._matched_timeout
    #         if req_and_sent_prompt:
    #             req_and_sent_prompt = req_and_sent_prompt and self._matched_prompt
    #         if req_and_sent_timeout:
    #             req_and_sent_timeout = req_and_sent_timeout and self._matched_timeout
    #     terminal_cmds_sent = ((both_requested and both_sent) or req_and_sent_timeout or req_and_sent_prompt)
    #     return terminal_cmds_sent and additional_commands_sent

    # def _sent_additional_settings_commands(self) -> bool:
    #     """
    #     Checks if additional commands after connection established are sent (useful for telnet, not used for ssh).
    #
    #     :return: True if all additional commands are sent (if any). False if any command left in the queue.
    #     """
    #     return True

    @abc.abstractmethod
    def build_command_string(self) -> str:
        """
        Returns string with command constructed with parameters of object.

        :return:  String with command.
        """
