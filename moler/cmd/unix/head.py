# -*- coding: utf-8 -*-
"""
Head command module.
"""
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone
import re

__author__ = 'Mateusz Szczurek, Sylwester Golonka'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'mateusz.m.szczurek@nokia.com, sylwester.golonka@nokia.com'


class Head(GenericUnixCommand):
    """Head command class."""

    def __init__(self, connection, path, options=None, prompt=None, newline_chars=None, runner=None):
        """
        Head command.

        :param connection: Moler connection to device, terminal when command is executed.
        :param path: Path to the file.
        :param options: Options of head command.
        :param prompt: Expected prompt that has been sent by device after command execution.
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        """
        super(Head, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.path = path
        self.options = options
        self.current_ret["LINES"] = []

    def build_command_string(self):
        """
        Build command string from parameters passed to object.

        :return: String representation of the command to send over a connection to the device.
        """
        cmd = "head"
        if self.options:
            cmd = f"{cmd} {self.path} {self.options}"
        else:
            cmd = f"{cmd} {self.path}"
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Put your parsing code here.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise.
        :return: None
        """
        if is_full_line:
            try:
                self._parse_error(line)
                self._parse_line(line)
            except ParsingDone:
                pass
        return super(Head, self).on_new_line(line, is_full_line)

    _re_parse_error = re.compile(r'head:\s(?P<PATH>.*):\s(?P<ERROR>.*)')

    def _parse_error(self, line):
        """
        Parse errors in line and set exception in case of any errors were parsed.

        :param line: Line to process.
        :return: None but raises ParsingDone if line has the information to handle by this method.
        """
        if self._regex_helper.search_compiled(Head._re_parse_error, line):
            self.set_exception(CommandFailure(self, f"ERROR: {self._regex_helper.group('ERROR')}"))
            raise ParsingDone

    def _parse_line(self, line):
        """
        Append line to LINES list.

        :param line: Line to process.
        :return: None but raises ParsingDone if line has the information to handle by this method.
        """
        self.current_ret["LINES"].append(line)
        raise ParsingDone


COMMAND_OUTPUT_no_options = """
host:~ # head /proc/meminfo
MemTotal:        4056916 kB
MemFree:         2035136 kB
MemAvailable:    2698056 kB
Buffers:           46040 kB
Cached:           782500 kB
SwapCached:            0 kB
Active:          1335448 kB
Inactive:         569004 kB
Active(anon):    1076756 kB
Inactive(anon):    17844 kB
host:~ # """

COMMAND_RESULT_no_options = {'LINES': ['MemTotal:        4056916 kB',
                                       'MemFree:         2035136 kB',
                                       'MemAvailable:    2698056 kB',
                                       'Buffers:           46040 kB',
                                       'Cached:           782500 kB',
                                       'SwapCached:            0 kB',
                                       'Active:          1335448 kB',
                                       'Inactive:         569004 kB',
                                       'Active(anon):    1076756 kB',
                                       'Inactive(anon):    17844 kB']
                             }

COMMAND_KWARGS_no_options = {
    "path": "/proc/meminfo"
}

COMMAND_OUTPUT_options = """
host:~ # head /proc/meminfo -n 3
MemTotal:        4056916 kB
MemFree:         1556208 kB
MemAvailable:    2369852 kB
host:~ # """

COMMAND_RESULT_options = {'LINES': ['MemTotal:        4056916 kB',
                                    'MemFree:         1556208 kB',
                                    'MemAvailable:    2369852 kB']
                          }

COMMAND_KWARGS_options = {
    "path": "/proc/meminfo",
    "options": "-n 3"
}
