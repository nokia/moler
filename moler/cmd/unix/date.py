# -*- coding: utf-8 -*-
"""
Date command module.
"""
import re

from moler.cmd.unix.genericunix import GenericUnix

__author__ = 'Tomasz Krol'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'tomasz.krol@nokia.com'


class Date(GenericUnix):
    def __init__(self, connection, prompt=None, new_line_chars=None):
        super(Date, self).__init__(connection, prompt=prompt, new_line_chars=new_line_chars)

        # Parameters defined by calling the command

        # Compiled regexp
        self._re_date_line = re.compile(r"DATE:\s+((\d+)-(\d+)-(\d+))", re.IGNORECASE)
        self._re_time_line = re.compile(r"TIME:\s+((\d+):(\d+):(\d+))", re.IGNORECASE)
        self._re_timezone_line = re.compile(r"ZONE:\s+(([-+])(\d{2})(\d{2})\s+(\w+))", re.IGNORECASE)
        self._re_epoch_line = re.compile(r"EPOCH:\s+(\d+)", re.IGNORECASE)
        self._re_week_number_line = re.compile(r"WEEK_NUMBER:\s+(\d+)", re.IGNORECASE)
        self._re_day_of_year_line = re.compile(r"DAY_OF_YEAR:\s+(\d+)", re.IGNORECASE)
        self._re_day_of_week_line = re.compile(r"DAY_OF_WEEK:\s+(\d+)\s+\((\w+)\)", re.IGNORECASE)
        self._re_month_line = re.compile(r"MONTH:\s+(\d+)\s+\((\w+)\)", re.IGNORECASE)

    def get_cmd(self, cmd=None):
        if not cmd:
            cmd = """date \
'+DATE:%t%t%d-%m-%Y%n\
TIME:%t%t%H:%M:%S%n\
ZONE:%t%t%z %Z%n\
EPOCH:%t%t%s%n\
WEEK_NUMBER:%t%-V%n\
DAY_OF_YEAR:%t%-j%n\
DAY_OF_WEEK:%t%u (%A)%n\
MONTH:%t%t%-m (%B)'"""
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            if self._regex_helper.search_compiled(self._re_date_line, line):
                self.current_ret["DATE"] = {
                    "FULL": self._regex_helper.group(1),
                    "DAY": self._regex_helper.group(2),
                    "MONTH": self._regex_helper.group(3),
                    "YEAR": self._regex_helper.group(4)
                }
                self.current_ret["DAY_OF_MONTH"] = int(self._regex_helper.group(2))
            elif self._regex_helper.search_compiled(self._re_time_line, line):
                self.current_ret["TIME"] = {
                    "FULL": self._regex_helper.group(1),
                    "HOUR": self._regex_helper.group(2),
                    "MINUTE": self._regex_helper.group(3),
                    "SECOND": self._regex_helper.group(4)
                }
            elif self._regex_helper.search_compiled(self._re_timezone_line, line):
                self.current_ret["ZONE"] = {
                    "FULL": self._regex_helper.group(1),
                    "SIGN": self._regex_helper.group(2),
                    "HOUR": self._regex_helper.group(3),
                    "MINUTE": self._regex_helper.group(4),
                    "NAME": self._regex_helper.group(5)
                }
            elif self._regex_helper.search_compiled(self._re_epoch_line, line):
                self.current_ret["EPOCH"] = int(self._regex_helper.group(1))
            elif self._regex_helper.search_compiled(self._re_week_number_line, line):
                self.current_ret["WEEK_NUMBER"] = int(self._regex_helper.group(1))
            elif self._regex_helper.search_compiled(self._re_day_of_year_line, line):
                self.current_ret["DAY_OF_YEAR"] = int(self._regex_helper.group(1))
            elif self._regex_helper.search_compiled(self._re_day_of_week_line, line):
                self.current_ret["DAY_OF_WEEK"] = int(self._regex_helper.group(1))
                self.current_ret["DAY_NAME"] = self._regex_helper.group(2)
            elif self._regex_helper.search_compiled(self._re_month_line, line):
                self.current_ret["MONTH_NUMBER"] = int(self._regex_helper.group(1))
                self.current_ret["MONTH_NAME"] = self._regex_helper.group(2)
        return super(Date, self).on_new_line(line, is_full_line)


COMMAND_OUTPUT = """
tkrol@belvedere01:~> date '+DATE:%t%t%d-%m-%Y%nTIME:%t%t%H:%M:%S%nZONE:%t%t%z %Z%nEPOCH:%t%t%s%nWEEK_NUMBER:%t%-V%nDAY_OF_YEAR:%t%-j%nDAY_OF_WEEK:%t%u (%A)%nMONTH:%t%t%-m (%B)'
DATE:           14-03-2018
TIME:           14:38:18
ZONE:           +0100 CET
EPOCH:          1521034698
WEEK_NUMBER:    11
DAY_OF_YEAR:    73
DAY_OF_WEEK:    3 (Wednesday)
MONTH:          3 (March)
tkrol@belvedere01:~>"""

COMMAND_RESULT = {
        'DATE': {
            'FULL': '14-03-2018',
            'YEAR': '2018',
            'MONTH': '03',
            'DAY': '14'
        },
        'DAY_NAME': 'Wednesday',
        'DAY_OF_YEAR': 73,
        'DAY_OF_MONTH': 14,
        'DAY_OF_WEEK': 3,
        'EPOCH': 1521034698,
        'MONTH_NAME': 'March',
        'MONTH_NUMBER': 3,
        'TIME': {
            'FULL': '14:38:18',
            'MINUTE': '38',
            'HOUR': '14',
            'SECOND': '18',
        },
        'WEEK_NUMBER': 11,
        'ZONE': {
            'FULL': '+0100 CET',
            'SIGN': '+',
            'HOUR': '01',
            'MINUTE': '00',
            'NAME': 'CET'
        }
    }

COMMAND_KWARGS = {}
