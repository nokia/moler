# -*- coding: utf-8 -*-
"""
Ctrl+C command module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2019-2025, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import re
from moler.cmd.commandchangingprompt import CommandChangingPrompt
from moler.cmd.commandtextualgeneric import CommandTextualGeneric


class CtrlC(CommandChangingPrompt):

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
        super(CtrlC, self).__init__(connection=connection, prompt=prompt, expected_prompt=expected_prompt,
                                    newline_chars=newline_chars, runner=runner)
        self.ret_required = False
        self.break_on_timeout = False  # If True then Ctrl+c on timeout
        self.newline_after_command_string = False  # Do not send newline after command string

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

    def send_command(self) -> None:
        """
        Sends command string to the device.

        :return: None
        """
        super().send_command()
        self._cmd_output_started = True  # Some terminals do not echo ctrl+c


COMMAND_OUTPUT = """
prompt>^C
bash-4.2:~ #"""

COMMAND_KWARGS = {
    "expected_prompt": r'bash-4.2'
}

COMMAND_RESULT = {}
