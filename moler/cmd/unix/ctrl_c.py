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

    def __init__(self, connection, prompt=None, expected_prompt=None, newline_chars=None, runner=None,
                 set_timeout=None, set_prompt=None, target_newline="\n", allowed_newline_after_prompt=True,
                 prompt_after_login=None):
        """
        Unix ctrl+c command

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
        super(CtrlC, self).__init__(connection=connection, prompt=prompt, expected_prompt=expected_prompt,
                                    newline_chars=newline_chars, runner=runner,
                                    set_timeout=set_timeout, set_prompt=set_prompt,
                                    target_newline=target_newline,
                                    prompt_after_login=prompt_after_login,
                                    allowed_newline_after_prompt=allowed_newline_after_prompt
                                    )
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
