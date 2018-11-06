# -*- coding: utf-8 -*-
"""
Uptime command module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import re
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone


class Uptime(GenericUnixCommand):
    # Compiled regexp

    def __init__(self, connection, options=None, prompt=None, newline_chars=None, runner=None):
        super(Uptime, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        # Parameters defined by calling the command
        self.options = options

    def build_command_string(self):
        cmd = "uptime"
        if self.options:
            cmd = "{} {}".format(cmd, self.options)
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_uptime(line)
                self._parse_since(line)
            except ParsingDone:
                pass
        return super(Uptime, self).on_new_line(line, is_full_line)

    # Linux:
    # 10:38am  up 3 days  2:14,  29 users,  load average: 0.09, 0.10, 0.07
    # SunOs:
    # 1:16am  up 137 day(s), 19:07,  1 user,  load average: 0.27, 0.27, 0.27
    _re_uptime_line = re.compile(r"\s+up\s+(?P<UPTIME_VAL>\S.*\S),\s+(?P<USERS>\d+)\s+user.*", re.IGNORECASE)

    # 137 day(s), 19:07
    # 3 days  2:14
    _re_days = re.compile(r"(?P<DAYS>\d+) day(.*),\s+(?P<HRS>\d+):(?P<MINS>\d+)")

    # 2 day(s), 3 min
    _re_days_minutes = re.compile(r"(?P<DAYS>\d+) day(.*),\s+(?P<MINS>\d+)\s+min")

    # 1:24
    _re_hours_minutes = re.compile(r"(?P<HRS>\d+):(?P<MINS>\d+)")

    # 18 min
    _re_minutes = re.compile(r"(?P<MINS>\d+) min")

    def _parse_uptime(self, line):
        if self._regex_helper.search_compiled(Uptime._re_uptime_line, line):
            val = self._regex_helper.group("UPTIME_VAL")
            users = int(self._regex_helper.group("USERS"))
            uptime_seconds = 0
            if self._regex_helper.search_compiled(Uptime._re_days, val):
                uptime_seconds = 24 * 3600 * int(self._regex_helper.group("DAYS")) + 3600 * int(
                    self._regex_helper.group("HRS")) + 60 * int(self._regex_helper.group("MINS"))
            elif self._regex_helper.search_compiled(Uptime._re_days_minutes, val):
                uptime_seconds = 24 * 3600 * int(self._regex_helper.group("DAYS")) + 3600 * int(
                    self._regex_helper.group("MINS"))
            elif self._regex_helper.search_compiled(Uptime._re_hours_minutes, val):
                uptime_seconds = 3600 * int(self._regex_helper.group("HRS")) + 60 * int(self._regex_helper.group("MINS"))
            elif self._regex_helper.search_compiled(self._re_minutes, val):
                uptime_seconds = 60 * int(self._regex_helper.group("MINS"))
            else:
                self.set_exception(CommandFailure(self, "Unsupported string format in line '{}'".format(line)))
            self.current_ret["UPTIME"] = val
            self.current_ret["UPTIME_SECONDS"] = uptime_seconds
            self.current_ret["USERS"] = users
            raise ParsingDone()

    # 2018-11-06 13:41:00
    _re_date_time = re.compile(r"(?P<DATE>\d{4}-\d{2}-\d{2})\s+(?P<TIME>\d{1,2}:\d{1,2}:\d{1,2})")

    def _parse_since(self, line):
        if self._regex_helper.search_compiled(Uptime._re_date_time, line):
            self.current_ret["date"] = self._regex_helper.group("DATE")
            self.current_ret["time"] = self._regex_helper.group("TIME")
            raise ParsingDone()

# -----------------------------------------------------------------------------
# Following documentation is required for library CI.
# It is used to perform command self-test.
# Parameters:
# file is Optional.File for Unix uptime command
# -----------------------------------------------------------------------------

COMMAND_OUTPUT_days_hours_minutes = """
host:~ # uptime
10:38am  up 3 days  2:14,  29 users,  load average: 0.09, 0.10, 0.07
host:~ #"""

COMMAND_KWARGS_days_hours_minutes = {}

COMMAND_RESULT_days_hours_minutes = {
    "UPTIME": '3 days  2:14',
    "UPTIME_SECONDS": 8040,
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

COMMAND_OUTPUT_since = """
host:~ # uptime -s
  2018-11-06 13:41:00
host:~ #"""

COMMAND_KWARGS_since = {'options': '-s'}

COMMAND_RESULT_since = {
    "date": "2018-11-06",
    "time": "13:41:00"
}
