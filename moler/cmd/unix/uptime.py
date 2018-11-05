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
    _re_uptime_line = re.compile(r"(?P<TIME>\d{2}:\d{2}:\d{2}|\d{2}:\d{2}(am|pm))\s+up\s+(?P<UPTIME_VAL>.*?),\s+(?P<USERS>\d+)\s+user.*",
                                 re.IGNORECASE)
    _re_days = re.compile(r"(\d+) day(?:s)?,\s+(\d+):(\d+)")
    _re_days_minutes = re.compile(r"(\d+) day(?:s)?,\s+(\d+)\s+min")
    _re_hours_minutes = re.compile(r"(?P<HOURS>\d+):(?P<MINS>\d+)")
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
            if self._regex_helper.search_compiled(Uptime._re_uptime_line, line):
                val = self._regex_helper.group("UPTIME_VAL")
                users = self._regex_helper.group("USERS")
                uptime_seconds = 0
                if self._regex_helper.search_compiled(Uptime._re_days, val):
                    uptime_seconds = 24 * 3600 * int(self._regex_helper.group(1)) + 3600 * int(
                        self._regex_helper.group(2)) + 60 * int(self._regex_helper.group(3))
                elif self._regex_helper.search_compiled(Uptime._re_days_minutes, val):
                    uptime_seconds = 24 * 3600 * int(self._regex_helper.group(1)) + 3600 * int(self._regex_helper.group(2))
                elif self._regex_helper.search_compiled(Uptime._re_hours_minutes, val):
                    uptime_seconds = 3600 * int(self._regex_helper.group(1)) + 60 * int(self._regex_helper.group(2))
                elif self._regex_helper.search_compiled(self._re_minutes, val):
                    uptime_seconds = 60 * int(self._regex_helper.group("MINS"))
                else:
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
    "USERS": '29'
}

COMMAND_OUTPUT_minutes = """
host:~ # uptime
10:38am  up 4 minutes,  29 users,  load average: 0.09, 0.10, 0.07
host:~ #"""

COMMAND_KWARGS_minutes = {}

COMMAND_RESULT_minutes = {
    "UPTIME": '4 minutes',
    "UPTIME_SECONDS": 240,
    "USERS": '29'
}
l