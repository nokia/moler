# -*- coding: utf-8 -*-
"""
Shasum command module.
"""
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone
import re

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'marcin.usielski@nokia.com'


class Shasum(GenericUnixCommand):
    def __init__(self, connection, path, options=None, cmd_kind='shasum', prompt=None, newline_chars=None, runner=None):
        """
        Moler base class for commands that change prompt.

        :param connection: moler connection to device, terminal when command is executed.
        :param path: path to file(s) to calculate sum.
        :param cmd_kind: command to calculate sum, eg. sha256sum, sha224sum or shasum.
        :param prompt: prompt on start system (where command starts).
        :param newline_chars: characters to split lines.
        :param runner: Runner to run command.
        """
        super(Shasum, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.path = path
        self.options = options
        self.cmd_kind = cmd_kind

    def build_command_string(self):
        """
        Builds command string form parameters.

        :return: Command string
        """
        cmd = self.cmd_kind
        if self.options:
            cmd = "{} {} {}".format(cmd, self.path, self.options)
        else:
            cmd = "{} {}".format(cmd, self.path)
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Parses every line from connection.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: None
        """
        if is_full_line:
            try:
                self._parse_sum(line)
            except ParsingDone:
                pass
        return super(Shasum, self).on_new_line(line, is_full_line)

    _re_parse_sum = re.compile(r'(?P<SUM>[\da-f]+)\s+(?P<FILE>\S+)')

    def _parse_sum(self, line):
        """
        Parses sum from command output.

        :param line: Line from device/connection.
        :return: None
        :raises ParsingDone if line was processed by the method.
        """
        if self._regex_helper.search_compiled(Shasum._re_parse_sum, line):
            file = self._regex_helper.group("FILE")
            shasum = self._regex_helper.group("SUM")
            self.current_ret['SUM'] = shasum
            self.current_ret['FILE'] = file
            if "FILES" not in self.current_ret:
                self.current_ret['FILES'] = dict()
            self.current_ret['FILES'][file] = shasum
        raise ParsingDone()


COMMAND_OUTPUT_parms = """
shasum test.txt
91503d6cac7a663901b30fc400e93644  test.txt
user@server:~$"""

COMMAND_RESULT_parms = {
    'FILE': 'test.txt',
    'SUM': '91503d6cac7a663901b30fc400e93644',
    'FILES': {
        'test.txt': '91503d6cac7a663901b30fc400e93644',
    }
}

COMMAND_KWARGS_parms = {
    "path": "test.txt",
}
