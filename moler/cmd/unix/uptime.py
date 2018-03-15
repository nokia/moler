# -*- coding: utf-8 -*-
"""
Uptime command module.
"""
from re import compile, escape, IGNORECASE

from moler.cmd.unix.genericunix import GenericUnix

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'


class Uptime(GenericUnix):
    #Compiled regexp
    _reg_uptime_line = compile(r"(\d{2}:\d{2}:\d{2}|\d{2}:\d{2}(am|pm))\s+up\s+(.*?),\s+(\d+)\s+user.*\n",
                                    IGNORECASE)
    _reg_days = compile(r"(\d+) day(?:s)?,\s+(\d+):(\d+)")
    _reg_days_minutes = compile(r"(\d+) day(?:s)?,\s+(\d+)\s+min")
    _reg_hours_minutes = compile(r"(\d+):(\d+)")
    _reg_minutes = compile(r"(\d+) min")

    def __init__(self, connection, file=None):
        super(Uptime, self).__init__(connection)

        # Parameters defined by calling the command
        self.file = file
        self.get_cmd()


    def get_cmd(self, cmd=None):
        if cmd is None:
            cmd = "uptime"
            if self.file:
                cmd = cmd + " " + self.file
        return cmd

    def on_new_line(self, line):
        if self._cmd_matched and self._regex_helper.search_compiled(Uptime._reg_uptime_line, line):
            val = self._regex_helper.group(3)
            users = self._regex_helper.group(4)
            uptime_seconds = 0
            if self._regex_helper.search_compiled(Uptime._reg_days, val):
                uptime_seconds = 24 * 3600 * int(self._regex_helper.group(1)) + 3600 * int(
                    self._regex_helper.group(2)) + 60 * int(self._regex_helper.group(3))
            elif self._regex_helper.search_compiled(Uptime._reg_days_minutes, val):
                uptime_seconds = 24 * 3600 * int(self._regex_helper.group(1)) + 3600 * int(self._regex_helper.group(2))
            elif self._regex_helper.search_compiled(Uptime._reg_hours_minutes, val):
                uptime_seconds = 3600 * int(self._regex_helper.group(1)) + 60 * int(self._regex_helper.group(2))
            elif self._regex_helper.search_compiled(self._reg_minutes, val):
                uptime_seconds = 60 * int(self._regex_helper.group(1))
            else:
                self.set_exception(Exception("Unsupported string format in line '{}'".format(line)))
            self.ret["UPTIME"] = val
            self.ret["UPTIME_SECONDS"] = uptime_seconds
            self.ret["USERS"] = users
        return super(Uptime, self).on_new_line(line)


# -----------------------------------------------------------------------------
# Following documentation is required for library CI.
# It is used to perform command self-test.
# Parameters:
# file is Optional.File for Unix uptime command
# -----------------------------------------------------------------------------

COMMAND_OUTPUT_ver_execute = """
fzm-tdd-1:~ # uptime
10:38am  up 3 days  2:14,  29 users,  load average: 0.09, 0.10, 0.07
fzm-tdd-1:~ #  
"""

COMMAND_KWARGS_ver_execute = {}

COMMAND_RESULT_ver_execute = {
            "UPTIME": '3 days  2:14',
            "UPTIME_SECONDS": 8040,
            "USERS": '29',
}

