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


class Uptime(GenericUnixCommand):
    # Compiled regexp

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
    _re_hours_minutes = re.compile(r"(?P<HRS>\d+):(?P<MINS>\d+)")
    _re_minutes = re.compile(r"(?P<MINS>\d+) min")

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
            print("Line '{}'".format(line))
            if self._regex_helper.search_compiled(Uptime._re_uptime_line, line):
                val = self._regex_helper.group("UPTIME_VAL")
                users = int(self._regex_helper.group("USERS"))
                print("Matched val:'{}' users:'{}'".format(val, users))
                uptime_seconds = 0
                if self._regex_helper.search_compiled(Uptime._re_days, val):
                    uptime_seconds = 24 * 3600 * int(self._regex_helper.group("DAYS")) + 3600 * int(
                        self._regex_helper.group("HRS")) + 60 * int(self._regex_helper.group("MINS"))
                elif self._regex_helper.search_compiled(Uptime._re_days_minutes, val):
                    print("2")
                    uptime_seconds = 24 * 3600 * int(self._regex_helper.group(1)) + 3600 * int(self._regex_helper.group(2))
                elif self._regex_helper.search_compiled(Uptime._re_hours_minutes, val):
                    print("3")
                    uptime_seconds = 3600 * int(self._regex_helper.group(1)) + 60 * int(self._regex_helper.group(2))
                elif self._regex_helper.search_compiled(self._re_minutes, val):
                    print("4")
                    uptime_seconds = 60 * int(self._regex_helper.group("MINS"))
                else:
                    print("5")
                    self.set_exception(CommandFailure(self, "Unsupported string format in line '{}'".format(line)))
                self.current_ret["UPTIME"] = val
                self.current_ret["UPTIME_SECONDS"] = uptime_seconds
                self.current_ret["USERS"] = users
        return super(Uptime, self).on_new_line(line, is_full_line)


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
  1:16am  up 137 day(s), 19:07,  1 user,  load average: 0.27, 0.27, 0.27
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
10:38am  up 4 minutes,  29 users,  load average: 0.09, 0.10, 0.07
host:~ #"""

COMMAND_KWARGS_minutes = {}

COMMAND_RESULT_minutes = {
    "UPTIME": '4 minutes',
    "UPTIME_SECONDS": 240,
    "USERS": 29
}
