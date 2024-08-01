# -*- coding: utf-8 -*-
"""
Uptime command module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2024, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import re
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone
from moler.util.converterhelper import ConverterHelper


class Uptime(GenericUnixCommand):

    def __init__(self, connection, options=None, prompt=None, newline_chars=None, runner=None):
        """
        :param connection: Moler connection to device, terminal when command is executed.
        :param options: uptime unix command options
        :param prompt: prompt (on system where command runs).
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        """
        super(Uptime, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        # Parameters defined by calling the command
        self.options = options

        self._converter_helper = ConverterHelper.get_converter_helper()

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.
        :return: String representation of command to send over connection to device.
        """
        cmd = "uptime"
        if self.options:
            cmd = f"{cmd} {self.options}"
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
                self._parse_uptime(line)
                self._parse_since(line)
            except ParsingDone:
                pass
        return super(Uptime, self).on_new_line(line, is_full_line)

    # Linux:
    # 10:38am  up 3 days  2:14,  29 users,  load average: 0.09, 0.10, 0.07
    # 09:11:11 up  1:17,  load average: 0.42, 0.51, 0.50
    # 11:39:09 up 3 min,  load average: 1.27, 1.08, 0.47
    # SunOs:
    # 1:16am  up 137 day(s), 19:07,  1 user,  load average: 0.27, 0.27, 0.27
    _re_uptime_line = re.compile(r"\s+up\s+(?P<UPTIME_VAL>\S.*\S),\s+(?P<USERS>\d+)\s+user.*", re.IGNORECASE)
    _re_uptime_line_no_user = re.compile(r"\s+up\s+(?P<UPTIME_VAL>\S.*\S),(\s*load average:.*)", re.IGNORECASE)

    def _parse_uptime(self, line):
        """
        Parses uptime from device.
        :param line: Line from device.
        :return: None but raises ParsingDone if line matches regex.
        """
        if self._regex_helper.search_compiled(Uptime._re_uptime_line, line) or \
                self._regex_helper.search_compiled(Uptime._re_uptime_line_no_user, line):
            values = self._regex_helper.groupdict()
            val = values.get("UPTIME_VAL")
            users = self._converter_helper.to_number(values["USERS"]) if values.get("USERS") else None
            uptime_seconds = self._calculate_seconds(val, line)
            self.current_ret["UPTIME"] = val
            self.current_ret["UPTIME_SECONDS"] = uptime_seconds
            self.current_ret["USERS"] = users
            raise ParsingDone()

    # 137 day(s), 19:07
    # 3 days  2:14
    _re_days = re.compile(r"(?P<DAYS>\d+) day(.*),?\s+(?P<HRS>\d+):(?P<MINS>\d+)")

    # 2 day(s), 3 min
    _re_days_minutes = re.compile(r"(?P<DAYS>\d+) day(.*),\s+(?P<MINS>\d+)\s+min")

    # 1:24
    _re_hours_minutes = re.compile(r"(?P<HRS>\d+):(?P<MINS>\d+)")

    # 18 min
    _re_minutes = re.compile(r"(?P<MINS>\d+) min")

    def _calculate_seconds(self, val_str, line):
        """
        Calculates seconds from fragment of output with time.
        :param val_str: Fragment with time.
        :param line: Line from device.
        :return: Int of seconds, converted from passed time.
        """
        seconds = 0
        if self._regex_helper.search_compiled(Uptime._re_days, val_str):
            seconds = 24 * 3600 * self._converter_helper.to_number(self._regex_helper.group("DAYS")) + 3600 * self._converter_helper.to_number(
                self._regex_helper.group("HRS")) + 60 * self._converter_helper.to_number(self._regex_helper.group("MINS"))
        elif self._regex_helper.search_compiled(Uptime._re_days_minutes, val_str):
            seconds = 24 * 3600 * self._converter_helper.to_number(self._regex_helper.group("DAYS")) + 60 * self._converter_helper.to_number(
                self._regex_helper.group("MINS"))
        elif self._regex_helper.search_compiled(Uptime._re_hours_minutes, val_str):
            seconds = 3600 * self._converter_helper.to_number(self._regex_helper.group("HRS")) + 60 * self._converter_helper.to_number(self._regex_helper.group("MINS"))
        elif self._regex_helper.search_compiled(self._re_minutes, val_str):
            seconds = 60 * self._converter_helper.to_number(self._regex_helper.group("MINS"))
        else:
            self.set_exception(CommandFailure(self, f"Unsupported string format in line '{line}'"))
        return seconds

    # 2018-11-06 13:41:00
    _re_date_time = re.compile(r"(?P<DATE>\d{4}-\d{2}-\d{2})\s+(?P<TIME>\d{1,2}:\d{1,2}:\d{1,2})")

    def _parse_since(self, line):
        """
        Parses date and time from line since when system has started.
        :param line: Line from device
        :return: None but raises ParsingDone if regex matches.
        """
        if self._regex_helper.search_compiled(Uptime._re_date_time, line):
            self.current_ret["date"] = self._regex_helper.group("DATE")
            self.current_ret["time"] = self._regex_helper.group("TIME")
            raise ParsingDone()


# -----------------------------------------------------------------------------
# Following documentation is required for library CI.
# It is used to perform command self-test.
# -----------------------------------------------------------------------------

COMMAND_OUTPUT_days_hours_minutes = """
host:~ # uptime
10:38am  up 3 days  2:14,  29 users,  load average: 0.09, 0.10, 0.07
host:~ #"""

COMMAND_KWARGS_days_hours_minutes = {}

COMMAND_RESULT_days_hours_minutes = {
    "UPTIME": '3 days  2:14',
    "UPTIME_SECONDS": 267240,
    "USERS": 29
}

COMMAND_OUTPUT_sunos = """
[host] ~ > uptime
  1:16am  up 137 day(s), 19:07,  1 user,  load average: 0.27, 0.27, 0.27
[host] ~ >"""

COMMAND_KWARGS_sunos = {}

COMMAND_RESULT_sunos = {
    "UPTIME": '137 day(s), 19:07',
    "UPTIME_SECONDS": 11905620,
    "USERS": 1
}

COMMAND_OUTPUT_minutes = """
host:~ # uptime
 11:50:35 up 18 min,  1 user,  load average: 0.00, 0.02, 0.04
host:~ #"""

COMMAND_KWARGS_minutes = {}

COMMAND_RESULT_minutes = {
    "UPTIME": '18 min',
    "UPTIME_SECONDS": 1080,
    "USERS": 1
}

COMMAND_OUTPUT_hours_minutes = """
host:~ # uptime
  12:57:01 up  1:24,  1 user,  load average: 0.00, 0.00, 0.00
host:~ #"""

COMMAND_KWARGS_hours_minutes = {}

COMMAND_RESULT_hours_minutes = {
    "UPTIME": '1:24',
    "UPTIME_SECONDS": 5040,
    "USERS": 1
}

COMMAND_OUTPUT_days_minutes = """
host:~ # uptime
  12:57:01 up 2 days, 4 minutes,  1 user,  load average: 0.00, 0.00, 0.00
host:~ #"""

COMMAND_KWARGS_days_minutes = {}

COMMAND_RESULT_days_minutes = {
    "UPTIME": '2 days, 4 minutes',
    "UPTIME_SECONDS": 173040,
    "USERS": 1
}

COMMAND_OUTPUT_since = """
host:~ # uptime -s
  2018-11-06 13:41:00
host:~ #"""

COMMAND_KWARGS_since = {'options': '-s'}

COMMAND_RESULT_since = {
    "date": "2018-11-06",
    "time": "13:41:00"
}


COMMAND_OUTPUT_no_users = """uptime
09:11:11 up  1:17,  load average: 0.42, 0.51, 0.50
moler_bash# """


COMMAND_KWARGS_no_users = {}


COMMAND_RESULT_no_users = {
    "UPTIME": '1:17',
    "UPTIME_SECONDS": 4620,
    "USERS": None
}
