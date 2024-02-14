# -*- coding: utf-8 -*-
"""
Sysctl command module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2021, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone


class Sysctl(GenericUnixCommand):

    def __init__(self, connection, options=None, parameter=None, value=None, prompt=None,
                 newline_chars=None, runner=None):
        """
        Sysctl command.
        :param connection: moler connection to device, terminal when command is executed.
        :param options: options of ping command for unix.
        :param parameter: name of parameter to set.
        :param value: value of parameter to set.
        :param prompt: prompt on system where ping is executed.
        :param newline_chars: characters to split lines.
        :param runner: Runner to run command
        """
        super(Sysctl, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        # Parameters defined by calling the command
        self.options = options
        self.parameter = parameter
        self.value = value
        self.ret_required = False

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.
        :return: String representation of command to send over connection to device.
        """
        cmd = "sysctl"
        if self.options:
            cmd = f"{cmd} {self.options}"
        if self.parameter and self.value:
            cmd = f"{cmd} {{{self.parameter}={self.value}}}"
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
                self._parse_parameter_value(line)
            except ParsingDone:
                pass  # line has been fully parsed by one of above parse-methods
        return super(Sysctl, self).on_new_line(line, is_full_line)

    # kernel.random.uuid = c628a4ed-db43-44b1-b5e2-80ff823a345a
    _re_param_value = re.compile(r"(?P<PARAM>\S.*\S|\S+)\s+=\s+(?P<VALUE>\S.*\S|\S+)")

    def _parse_parameter_value(self, line):
        if self._regex_helper.search_compiled(Sysctl._re_param_value, line):
            self.current_ret[self._regex_helper.group("PARAM")] = self._regex_helper.group("VALUE")
            raise ParsingDone()


COMMAND_OUTPUT_all = """sysctl -a
fs.binfmt_misc.python3/5 = interpreter /usr/bin/python3.5
fs.inode-state = 165149	836	0	0	0	0	0
kernel.random.uuid = c628a4ed-db43-44b1-b5e2-80ff823a345a
moler_bash#"""
COMMAND_KWARGS_all = {'options': '-a'}

COMMAND_RESULT_all = {
    'fs.binfmt_misc.python3/5': 'interpreter /usr/bin/python3.5',
    'fs.inode-state': '165149	836	0	0	0	0	0',
    'kernel.random.uuid': 'c628a4ed-db43-44b1-b5e2-80ff823a345a'
}

COMMAND_OUTPUT_grep = """sysctl -a | grep inode
fs.inode-state = 165149	836	0	0	0	0	0
moler_bash#"""
COMMAND_KWARGS_grep = {'options': '-a | grep inode'}

COMMAND_RESULT_grep = {
    'fs.inode-state': '165149	836	0	0	0	0	0',
}

COMMAND_OUTPUT_w = """sysctl -w {kernel.ctrl-alt-del=0}
moler_bash#"""
COMMAND_KWARGS_w = {'options': '-w', 'parameter': 'kernel.ctrl-alt-del', 'value': '0'}

COMMAND_RESULT_w = {}
