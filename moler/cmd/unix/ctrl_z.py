# -*- coding: utf-8 -*-
"""
Ctrl+Z command module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2024, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import re
from moler.exceptions import ParsingDone
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

    def on_new_line(self, line: str, is_full_line: bool) -> None:
        """
        Method to parse line from device.

        :param line: Line from device.
        :param is_full_line: Flag marking if line is not partial.
        :return: None
        """
        if is_full_line:
            try:
                self._process_id(line)
            except ParsingDone:
                pass
        super(CtrlZ, self).on_new_line(line, is_full_line)

    # [2]+  Stopped                 ping 10.83.200.200
    _re_ctrl_z = re.compile(r'\[(?P<ID>\d+)\]\+\s+Stopped\s+(?P<PROCESS>.*)')

    def _process_id(self, line: str) -> None:
        """
        Method to parse line with process id.

        :param line: Line from device.
        :return: None
        """
        if self._regex_helper.search(CtrlZ._re_ctrl_z, line):
            self.current_ret['id'] = int(self._regex_helper.group('ID'))
            self.current_ret['process'] = self._regex_helper.group('PROCESS')
            raise ParsingDone()


COMMAND_OUTPUT = """
prompt>^Z
[2]+  Stopped                 myScript param1 param2
bash-4.2:~ #"""

COMMAND_KWARGS = {
    "expected_prompt": r'bash-4.2'
}

COMMAND_RESULT = {
    'id': 2,
    'process': 'myScript param1 param2',
}
