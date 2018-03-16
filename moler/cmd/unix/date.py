# -*- coding: utf-8 -*-
"""
Date command module.
"""
import re

from moler.cmd.unix.genericunix import GenericUnix

__author__ = 'Tomasz Kroli'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'tomasz.krol@nokia.com'


class Date(GenericUnix):
    def __init__(self, connection):
        super(Date, self).__init__(connection)

        # Parameters defined by calling the command
        self.command_string = self.get_cmd()

        # Compiled regexp
        self._re_date_line = re.compile(r"DATE:\s+((\d+)-(\d+)-(\d+)).*\n", re.IGNORECASE)
        self._re_time_line = re.compile(r"TIME:\s+((\d+):(\d+):(\d+)).*\n", re.IGNORECASE)
        self._re_timezone_line = re.compile(r"ZONE:\s+(([-+])(\d{2})(\d{2})\s+(\w+)).*\n", re.IGNORECASE)
        self._re_epoch_line = re.compile(r"EPOCH:\s+(\d+).*\n", re.IGNORECASE)
        self._re_week_number_line = re.compile(r"WEEK_NUMBER:\s+(\d+).*\n", re.IGNORECASE)
        self._re_day_of_year_line = re.compile(r"DAY_OF_YEAR:\s+(\d+).*\n", re.IGNORECASE)
        self._re_day_of_week_line = re.compile(r"DAY_OF_WEEK:\s+(\d+)\s+\((\w+)\).*\n", re.IGNORECASE)
        self._re_month_line = re.compile(r"MONTH:\s+(\d+)\s+\((\w+)\).*\n", re.IGNORECASE)

    def get_cmd(self, cmd=None):
        cmd = """date \
'+DATE:%t%t%d-%m-%Y%n\
TIME:%t%t%H:%M:%S%n\
ZONE:%t%t%z %Z%n\
EPOCH:%t%t%s%n\
WEEK_NUMBER:%t%-V%n\
DAY_OF_YEAR:%t%-j%n\
DAY_OF_WEEK:%t%u (%A)%n\
MONTH:%t%t%-m (%B)'"""

        self.command_string = cmd
        self._cmd_escaped = re.escape(cmd)
        return cmd

    def on_new_line(self, line):
        if self._cmd_matched:
            if self._regex_helper.search_compiled(self._re_date_line, line):
                self.ret["DATE"] = {
                    "FULL": self._regex_helper.group(1),
                    "DAY": self._regex_helper.group(2),
                    "MONTH": self._regex_helper.group(3),
                    "YEAR": self._regex_helper.group(4)
                }
                self.ret["DAY_OF_MONTH"] = int(self._regex_helper.group(2))
            elif self._regex_helper.search_compiled(self._re_time_line, line):
                self.ret["TIME"] = {
                    "FULL": self._regex_helper.group(1),
                    "HOUR": self._regex_helper.group(2),
                    "MINUTE": self._regex_helper.group(3),
                    "SECOND": self._regex_helper.group(4)
                }
            elif self._regex_helper.search_compiled(self._re_timezone_line, line):
                self.ret["ZONE"] = {
                    "FULL": self._regex_helper.group(1),
                    "SIGN": self._regex_helper.group(2),
                    "HOUR": self._regex_helper.group(3),
                    "MINUTE": self._regex_helper.group(4),
                    "NAME": self._regex_helper.group(5)
                }
            elif self._regex_helper.search_compiled(self._re_epoch_line, line):
                self.ret["EPOCH"] = int(self._regex_helper.group(1))
            elif self._regex_helper.search_compiled(self._re_week_number_line, line):
                self.ret["WEEK_NUMBER"] = int(self._regex_helper.group(1))
            elif self._regex_helper.search_compiled(self._re_day_of_year_line, line):
                self.ret["DAY_OF_YEAR"] = int(self._regex_helper.group(1))
            elif self._regex_helper.search_compiled(self._re_day_of_week_line, line):
                self.ret["DAY_OF_WEEK"] = int(self._regex_helper.group(1))
                self.ret["DAY_NAME"] = self._regex_helper.group(2)
            elif self._regex_helper.search_compiled(self._re_month_line, line):
                self.ret["MONTH_NUMBER"] = int(self._regex_helper.group(1))
                self.ret["MONTH_NAME"] = self._regex_helper.group(2)
        return super(Date, self).on_new_line(line)
