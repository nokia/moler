# -*- coding: utf-8 -*-
"""
Command time module
"""


__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2024, Nokia'
__email__ = 'marcin.usielski@nokia.com'

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone
import re


class Time(GenericUnixCommand):

    def __init__(self, connection, options: str=None, prompt=None, newline_chars=None, runner=None):
        """
        Unix command time.

        :param connection: Moler connection to device, terminal when command is executed.
        :param options: Options of unix command time
        :param prompt: prompt (on system where command runs).
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.

        """
        super(Time, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.ret_required = False
        self.options = options

    def build_command_string(self):
        """
        Build the command string from parameters passed to object.

        :return: String representation of command to send over connection to device.
        """
        cmd = "time"
        if self.options is not None:
            cmd = "{} {}".format(cmd, self.options)
        return cmd

    def on_new_line(self, line: str, is_full_line: bool) -> None:
        """
        Method to parse output from command.

        :param line: Line from device.
        :param is_full_line: True if line is full (was the end line), False otherwise.
        """
        try:
            self._parse_time(line)
        except ParsingDone:
            pass
        return super().on_new_line(line, is_full_line)

    # real    0m0.000s
    _re_time = re.compile(r"^\s*(?P<type>real|user|sys)\s+(?P<value>(?P<min>\d+)m(?P<sec>\d+\.\d+)s)\s*$")

    def _parse_time(self, line: str):
        """
        Parse time line.

        :param line: Line from device.
        :return: None
        """
        if self._regex_helper.search_compiled(Time._re_time, line):
            type = self._regex_helper.group('type')
            self.current_ret[type] = dict()
            self.current_ret[type]['raw'] = self._regex_helper.group('value')
            self.current_ret[type]['sec'] = float(self._regex_helper.group('min')) * 60 + float(self._regex_helper.group('sec'))    # noqa
            raise ParsingDone()


COMMAND_OUTPUT = """time
real    0m0.000s
user    0m0.000s
sys     0m0.000s
moler_bash#"""


COMMAND_KWARGS = {}


COMMAND_RESULT = {
    'real': {
        'raw': '0m0.000s',
        'sec': 0.
    },
    'user': {
        'raw': '0m0.000s',
        'sec': 0.
    },
    'sys': {
        'raw': '0m0.000s',
        'sec': 0.
    }
}


COMMAND_OUTPUT_sleep_60 = """time sleep 60
real    1m0.004s
user    0m0.001s
sys     0m0.002s
moler_bash#"""


COMMAND_KWARGS_sleep_60 = {
    'options': 'sleep 60',
}


COMMAND_RESULT_sleep_60 = {
    'real': {
        'raw': '1m0.004s',
        'sec': 60.004
    },
    'user': {
        'raw': '0m0.001s',
        'sec': 0.001
    },
    'sys': {
        'raw': '0m0.002s',
        'sec': 0.002
    }
}
