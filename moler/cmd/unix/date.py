# -*- coding: utf-8 -*-
"""
Date command module.
"""

__author__ = 'Tomasz Krol, Michal Ernst'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'tomasz.krol@nokia.com, michal.ernst@nokia.com'

import re

from moler.cmd.unix.genericunix import GenericUnixCommand


class Date(GenericUnixCommand):
    def __init__(self, connection, options=None, date_table_output=True, prompt=None, newline_chars=None, runner=None):
        super(Date, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)

        self.ret_required = False
        self.options = options
        self.date_table_output = date_table_output

    def build_command_string(self):
        cmd = "date"

        if self.options:
            cmd = f"{cmd} {self.options}"

        if self.date_table_output:
            cmd = f"{cmd} \
'+DATE:%t%t%d-%m-%Y%n\
TIME:%t%t%H:%M:%S%n\
ZONE:%t%t%z %Z%n\
EPOCH:%t%t%s%n\
WEEK_NUMBER:%t%-V%n\
DAY_OF_YEAR:%t%-j%n\
DAY_OF_WEEK:%t%u (%A)%n\
MONTH:%t%t%-m (%B)'"

        return cmd

    # Compiled regexp
    _re_date_line = re.compile(r"DATE:\s+((\d+)-(\d+)-(\d+))", re.IGNORECASE)
    _re_time_line = re.compile(r"TIME:\s+((\d+):(\d+):(\d+))", re.IGNORECASE)
    _re_timezone_line = re.compile(r"ZONE:\s+(([-+])(\d{2})(\d{2})\s+(\w+))", re.IGNORECASE)
    _re_epoch_line = re.compile(r"EPOCH:\s+(\d+)", re.IGNORECASE)
    _re_week_number_line = re.compile(r"WEEK_NUMBER:\s+(\d+)", re.IGNORECASE)
    _re_day_of_year_line = re.compile(r"DAY_OF_YEAR:\s+(\d+)", re.IGNORECASE)
    _re_day_of_week_line = re.compile(r"DAY_OF_WEEK:\s+(\d+)\s+\((\w+)\)", re.IGNORECASE)
    _re_month_line = re.compile(r"MONTH:\s+(\d+)\s+\((\w+)\)", re.IGNORECASE)

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            if self._regex_helper.search_compiled(Date._re_date_line, line):
                self.current_ret["DATE"] = {
                    "FULL": self._regex_helper.group(1),
                    "DAY": self._regex_helper.group(2),
                    "MONTH": self._regex_helper.group(3),
                    "YEAR": self._regex_helper.group(4)
                }
                self.current_ret["DAY_OF_MONTH"] = int(self._regex_helper.group(2))
            elif self._regex_helper.search_compiled(Date._re_time_line, line):
                self.current_ret["TIME"] = {
                    "FULL": self._regex_helper.group(1),
                    "HOUR": self._regex_helper.group(2),
                    "MINUTE": self._regex_helper.group(3),
                    "SECOND": self._regex_helper.group(4)
                }
            elif self._regex_helper.search_compiled(Date._re_timezone_line, line):
                self.current_ret["ZONE"] = {
                    "FULL": self._regex_helper.group(1),
                    "SIGN": self._regex_helper.group(2),
                    "HOUR": self._regex_helper.group(3),
                    "MINUTE": self._regex_helper.group(4),
                    "NAME": self._regex_helper.group(5)
                }
            elif self._regex_helper.search_compiled(Date._re_epoch_line, line):
                self.current_ret["EPOCH"] = int(self._regex_helper.group(1))
            elif self._regex_helper.search_compiled(Date._re_week_number_line, line):
                self.current_ret["WEEK_NUMBER"] = int(self._regex_helper.group(1))
            elif self._regex_helper.search_compiled(Date._re_day_of_year_line, line):
                self.current_ret["DAY_OF_YEAR"] = int(self._regex_helper.group(1))
            elif self._regex_helper.search_compiled(Date._re_day_of_week_line, line):
                self.current_ret["DAY_OF_WEEK"] = int(self._regex_helper.group(1))
                self.current_ret["DAY_NAME"] = self._regex_helper.group(2)
            elif self._regex_helper.search_compiled(Date._re_month_line, line):
                self.current_ret["MONTH_NUMBER"] = int(self._regex_helper.group(1))
                self.current_ret["MONTH_NAME"] = self._regex_helper.group(2)
        return super(Date, self).on_new_line(line, is_full_line)


COMMAND_OUTPUT = """user@server:~> date '+DATE:%t%t%d-%m-%Y%nTIME:%t%t%H:%M:%S%nZONE:%t%t%z %Z%nEPOCH:%t%t%s%nWEEK_NUMBER:%t%-V%nDAY_OF_YEAR:%t%-j%nDAY_OF_WEEK:%t%u (%A)%nMONTH:%t%t%-m (%B)'
DATE:           14-03-2018
TIME:           14:38:18
ZONE:           +0100 CET
EPOCH:          1521034698
WEEK_NUMBER:    11
DAY_OF_YEAR:    73
DAY_OF_WEEK:    3 (Wednesday)
MONTH:          3 (March)
user@server:~>"""

COMMAND_KWARGS = {}

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

COMMAND_OUTPUT_with_options = """user@server:~> date -s "2021-01-01 00:00"
user@server:~>"""

COMMAND_KWARGS_with_options = {
    "options": "-s \"2021-01-01 00:00\""
}

COMMAND_RESULT_with_options = {}
