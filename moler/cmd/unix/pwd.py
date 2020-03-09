# -*- coding: utf-8 -*-
"""
pwd command module.
"""
import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone

__author__ = 'Yang Snackwell, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2020, Nokia'
__email__ = 'snackwell.yang@nokia-sbell.com, marcin.usielski@nokia.com'


class Pwd(GenericUnixCommand):

    def __init__(self, connection, prompt=None, newline_chars=None, runner=None, options=None):
        """
        Unix command pwd.

        :param connection: Moler connection to device, terminal when command is executed.
        :param prompt: prompt (on system where command runs).
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        :param options: Options of unix ls command
        """
        super(Pwd, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.ret_required = True
        self.options = options

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.

        :return: String representation of command to send over connection to device.
        """
        cmd = "pwd"
        if self.options:
            cmd = "{} {}".format(cmd, self.options)
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Processes line from output form connection/device.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise.
        :return: None.
        """
        if is_full_line:
            try:
                self._parse_pwd_line(line)
            except ParsingDone:
                pass
        return super(Pwd, self).on_new_line(line, is_full_line)

    _re_pwd_line = re.compile(r"^(?P<full_path>(?P<path_to_current>.*)/(?P<current_path>.*))$")

    def _parse_pwd_line(self, line):
        if self._regex_helper.search_compiled(self._re_pwd_line, line):
            self.current_ret = self._regex_helper.groupdict()
            raise ParsingDone


COMMAND_OUTPUT = """pwd
/home/tmp dir/xyz
moler_bash#"""

COMMAND_RESULT = {
    'current_path': 'xyz',
    'full_path': '/home/tmp dir/xyz',
    'path_to_current': '/home/tmp dir'
}

COMMAND_KWARGS = {}

COMMAND_OUTPUT_with_p = """pwd -P
/home/tmp dir/xyz
moler_bash#"""

COMMAND_RESULT_with_p = {
    'current_path': 'xyz',
    'full_path': '/home/tmp dir/xyz',
    'path_to_current': '/home/tmp dir'
}

COMMAND_KWARGS_with_p = {'options': '-P'}
