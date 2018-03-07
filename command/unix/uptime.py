"""
:copyright: Nokia Networks
:author: Marcin Usielski
:contact: marcin.usielski@nokia.com
:maintainer:
:contact:
"""


import re
from genericunix import GenericUnix


class Uptime(GenericUnix):
    def __init__(self, connection, file=None):
        super(Uptime, self).__init__(connection)

        # Parameters defined by calling the command
        self.file = file
        self.command_string = self.get_cmd()

        # Compiled regexp
        self._reg_uptime_line = re.compile(r"(\d{2}:\d{2}:\d{2}|\d{2}:\d{2}(am|pm))\s+up\s+(.*?),\s+(\d+)\s+user.*\n",
                                           re.IGNORECASE)
        self._reg_days = re.compile(r"(\d+) day(?:s)?,\s+(\d+):(\d+)")
        self._reg_days_minutes = re.compile(r"(\d+) day(?:s)?,\s+(\d+)\s+min")
        self._reg_hours_minutes = re.compile(r"(\d+):(\d+)")
        self._reg_minutes = re.compile(r"(\d+) min")

    def get_cmd(self, cmd=None):
        if cmd is None:
            cmd = "uptime"
            if self.file:
                cmd = cmd + " " + self.file
        self.command_string = cmd
        self._cmd_escaped = re.escape(cmd)
        return cmd

    def on_new_line(self, line):
        if self._cmd_matched and self._regex_helper.search_compiled(self._reg_uptime_line, line):
            val = self._regex_helper.group(3)
            users = self._regex_helper.group(4)
            uptime_seconds = 0
            if self._regex_helper.search_compiled(self._reg_days, val):
                uptime_seconds = 24 * 3600 * int(self._regex_helper.group(1)) + 3600 * int(
                    self._regex_helper.group(2)) + 60 * int(self._regex_helper.group(3))
            elif self._regex_helper.search_compiled(self._reg_days_minutes, val):
                uptime_seconds = 24 * 3600 * int(self._regex_helper.group(1)) + 3600 * int(self._regex_helper.group(2))
            elif self._regex_helper.search_compiled(self._reg_hours_minutes, val):
                uptime_seconds = 3600 * int(self._regex_helper.group(1)) + 60 * int(self._regex_helper.group(2))
            elif self._regex_helper.search_compiled(self._reg_minutes, val):
                uptime_seconds = 60 * int(self._regex_helper.group(1))
            else:
                self.set_exception(Exception("Unsupported string format in line '%s'" (line)))
            self.ret["UPTIME"] = val
            self.ret["UPTIME_SECONDS"] = uptime_seconds
            self.ret["USERS"] = users
        return super(Uptime, self).on_new_line(line)
