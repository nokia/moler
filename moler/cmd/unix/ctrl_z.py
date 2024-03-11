# -*- coding: utf-8 -*-
"""
Ctrl+Z command module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2024, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import re
from moler.cmd.unix.ctrl_c import CtrlC


class CtrlZ(CtrlC):

    """Unix ctrl+z command"""

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.

        :return: String representation of command to send over connection to device.
        """
        return chr(0x1A)

    @property
    def command_string(self):
        """
        Getter for command_string.

        :return: String with command_string
        """
        if not self.__command_string:
            self.__command_string = self.build_command_string()
            self._cmd_escaped = re.compile(r"\^Z", re.I)
        return self.__command_string

    @command_string.setter
    def command_string(self, command_string):
        """
        Setter for command_string.

        :param command_string: String with command to set.
        :return: None
        """
        self.__command_string = command_string
        self._cmd_escaped = re.compile(r"\^Z", re.I)


COMMAND_OUTPUT = """
prompt>^Z
bash-4.2:~ #"""

COMMAND_KWARGS = {
    "expected_prompt": r'bash-4.2'
}

COMMAND_RESULT = {}
