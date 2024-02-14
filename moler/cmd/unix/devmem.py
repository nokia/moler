# -*- coding: utf-8 -*-
"""
Devmem command module.
"""

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone

__author__ = 'Sylwester Golonka, Michal Ernst'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'sylwester.golonka@nokia.com, michal.ernst@nokia.com'


class Devmem(GenericUnixCommand):
    """Devmem command class."""

    def __init__(self, connection, address, size=None, value=None, options=None, prompt=None, newline_chars=None,
                 runner=None):
        """
        Devmem command.

        :param connection: moler connection to device, terminal when command is executed.
        :param address: memory address
        :param size: size of variable (bites)
        :param value: value that will be set in memory
        :param options: parameter with which the command will be executed
        :param prompt: expected prompt sending by device after command execution
        :param newline_chars: Characters to split lines
        :param runner: Runner to run command
        """
        super(Devmem, self).__init__(connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.address = address
        self.value = value
        self.size = size
        self.options = options

    def build_command_string(self):
        """
        Build command string from parameters passed to object.

        :return: String representation of command to send over connection to device.
        """
        cmd = "devmem"
        if self.options:
            cmd = f"{cmd} {self.options}"
        cmd = f"{cmd} {self.address}"
        if self.size and self.value:
            cmd = f"{cmd} {self.size} {self.value}"
            self.ret_required = False
        elif self.value:
            cmd = f"{cmd} {self.value}"
            self.ret_required = False
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Put your parsing code here.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: None
        """
        if is_full_line:
            try:
                self._parse_memory_value(line)
            except ParsingDone:
                pass
        return super(Devmem, self).on_new_line(line, is_full_line)

    _re_memory_value = re.compile(r"(?P<VALUE>0x[\dABCDEF]+)")

    def _parse_memory_value(self, line):
        """
        Parse memory hexadecimal value in line.

        :param line: Line from device.
        :return: None but raises ParsingDone if line has information to handle by this method.
        """
        if self._regex_helper.search(Devmem._re_memory_value, line):
            self.current_ret["VALUE"] = self._regex_helper.group("VALUE")
            raise ParsingDone


COMMAND_OUTPUT = """
user@host:~# devmem -switches 0x01f00000 32 0x1000
user@host:~# """

COMMAND_KWARGS = {'address': '0x01f00000',
                  'value': '0x1000',
                  'size': '32',
                  'options': '-switches'}

COMMAND_RESULT = {}

COMMAND_OUTPUT_one_parameter = """
user@host:~# devmem 0x01f00000
0x1000
user@host:~# """

COMMAND_KWARGS_one_parameter = {'address': '0x01f00000'}

COMMAND_RESULT_one_parameter = {'VALUE': '0x1000'}

COMMAND_OUTPUT_change_value = """
user@host:~# devmem b 0x01f00000 255
user@host:~# """

COMMAND_KWARGS_change_value = {'options': 'b',
                               'address': '0x01f00000',
                               'value': '255'}

COMMAND_RESULT_change_value = {}
