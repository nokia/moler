# -*- coding: utf-8 -*-
"""
History command module.
"""

__author__ = 'Marcin Szlapa'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'marcin.szlapa@nokia.com'

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone
from moler.helpers import convert_to_number
import re


class History(GenericUnixCommand):
    """Unix command history."""

    def __init__(self, connection, prompt=None, newline_chars=None, runner=None):
        """
        Unix command history.
        :param connection: moler connection to device, terminal when command is executed
        :param prompt: expected prompt sending by device after command execution
        :param newline_chars: Characters to split lines
        :param runner: Runner to run command
        """
        super(History, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                      runner=runner)

    def build_command_string(self):
        """
        Build command string from parameters passed to object.
        :return: String representation of command to send over connection to device.
        """
        cmd = "history"
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
                self._parse_history(line)
            except ParsingDone:
                pass
        return super(History, self).on_new_line(line, is_full_line)

    #     8  cat directory/file
    _re_history = re.compile(r"\s*(?P<NUMBER>\d+)\s+(?P<CMD>.+)")

    def _parse_history(self, line):
        if self._regex_helper.search_compiled(History._re_history, line):
            self.current_ret[convert_to_number(self._regex_helper.group('NUMBER'))] = self._regex_helper.group('CMD')
        raise ParsingDone


COMMAND_OUTPUT_History = """host:~ # history
    1  ls
    2  cd /home/
    3  mkdir test
    4  ls -l
    5  rmdir test
    6  ip n
    7  mv file directory/
    8  cat directory/file
    9  cd ~
host:~ #"""

COMMAND_KWARGS_History = {
}

COMMAND_RESULT_History = {
    1: "ls",
    2: "cd /home/",
    3: "mkdir test",
    4: "ls -l",
    5: "rmdir test",
    6: "ip n",
    7: "mv file directory/",
    8: "cat directory/file",
    9: "cd ~"
}
