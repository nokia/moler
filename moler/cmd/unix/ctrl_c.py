# -*- coding: utf-8 -*-
"""
Ctrl+C command module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import re
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.cmd.commandtextualgeneric import CommandTextualGeneric


class CtrlC(GenericUnixCommand):

    """Unix ctrl+c command"""

    def __init__(self, connection, prompt=None, expected_prompt=None, newline_chars=None, runner=None):
        """
        Unix ctrl+c command

        :param connection: Moler connection to device, terminal when command is executed.
        :param prompt: Prompt of the starting shell
        :param expected_prompt: Prompt of the target shell reached after ctrl+c command
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        """
        super(CtrlC, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.ret_required = False
        self.break_on_timeout = False  # If True then Ctrl+c on timeout
        self.newline_after_command_string = False  # Do not send newline after command string
        self._re_expected_prompt = CommandTextualGeneric._calculate_prompt(expected_prompt)  # Expected prompt on device

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.

        :return: String representation of command to send over connection to device.
        """
        return chr(3)

    @property
    def command_string(self):
        """
        Getter for command_string.

        :return: String with command_string
        """
        if not self.__command_string:
            self.__command_string = self.build_command_string()
            self._cmd_escaped = re.compile(r"\^C", re.I)
        return self.__command_string

    @command_string.setter
    def command_string(self, command_string):
        """
        Setter for command_string.

        :param command_string: String with command to set.
        :return: None
        """
        self.__command_string = command_string
        self._cmd_escaped = re.compile(r"\^C", re.I)

    def on_new_line(self, line, is_full_line):
        """
        Parses the output of the command.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: None
        """
        if self._regex_helper.search_compiled(self._re_expected_prompt, line):
            if not self.done():
                self.set_result(self.current_ret)


COMMAND_OUTPUT = """
prompt>^C
bash-4.2:~ #"""

COMMAND_KWARGS = {
    "expected_prompt": r'bash-4.2'
}

COMMAND_RESULT = {}
