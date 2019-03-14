# -*- coding: utf-8 -*-
"""
lsof command module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'marcin.usielski@nokia.com'

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone
import re


class Lsof(GenericUnixCommand):

    """Unix lsof command"""

    def __init__(self, connection, prompt=None, newline_chars=None, runner=None, options=None):
        """
        Unix ctrl+c command

        :param connection: Moler connection to device, terminal when command is executed.
        :param prompt: Prompt of the starting shell
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        :param options: Options for command lsof
        """
        super(Lsof, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.options = options
        self._headers = list()
        self._header_pos = list()

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.

        :return: String representation of command to send over connection to device.
        """
        cmd = "lsof"
        if self.options:
            cmd = "lsof {}".format(self.options)
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Parses the output of the command.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: Nothing
        """
        if is_full_line:
            try:
                self._parse_headers(line)
                self._parse_data(line)
            except ParsingDone:
                pass
        super(Lsof, self).on_new_line(line=line, is_full_line=is_full_line)

    # COMMAND     PID   TID        USER   FD      TYPE             DEVICE  SIZE/OFF       NODE NAME
    _re_headers = re.compile(r"\S+")

    def _parse_headers(self, line):
        if not self._headers:
            self._headers = re.findall(Lsof._re_headers, line)
            for header in self._headers:
                position = line.find(header)
                self._header_pos.append(position)
            self.current_ret["HEADERS"] = self._headers
            self.current_ret["HEADER_POS"] = self._header_pos
            raise ParsingDone()

    def _parse_data(self, line):
        if self._headers:
            item=dict()



COMMAND_OUTPUT_no_parameters = """lsof
COMMAND     PID   TID        USER   FD      TYPE             DEVICE  SIZE/OFF       NODE NAME
systemd       1              root  cwd   unknown                                         /proc/1/cwd (readlink: Permission denied)
systemd       1              root  rtd   unknown                                         /proc/1/root (readlink: Permission denied)
lxpanel    1593               ute   12r     FIFO               0,10       0t0      20366 pipe
bash-4.2:~ #"""

COMMAND_KWARGS_no_parameters = {
}

COMMAND_RESULT_no_parameters = {}
