# -*- coding: utf-8 -*-
"""
AT+CFUN

AT commands specification:
google for: 3gpp specification 27.007
(always check against latest version of standard)
"""

__author__ = 'Kamil Pielka'
__copyright__ = 'Copyright (C) 2022, Nokia'
__email__ = 'kamik.pielka@nokia.com'

import re

from moler.cmd.at.genericat import GenericAtCommand
from moler.exceptions import ParsingDone


class GetFunctionalityLevel(GenericAtCommand):
    """
    Command to get UE's level of functionality. Example output:

    +CFUN: 1

    OK
    """
    def __init__(self, connection=None, prompt=None, newline_chars=None, runner=None):
        """Create instance of GetFunctionalityLevel class"""
        super(GetFunctionalityLevel, self).__init__(connection=connection, operation='execute', prompt=prompt,
                                                    newline_chars=newline_chars, runner=runner)

    def build_command_string(self):
        return "AT+CFUN?"

    def on_new_line(self, line, is_full_line):
        """
        Method to parse command output. Will be called after line with command echo.

        +CFUN: 1

        OK

        Write your own implementation but don't forget to call on_new_line from base class

        :param line: Line to parse, new lines are trimmed
        :param is_full_line:  False for chunk of line; True on full line (NOTE: new line character removed)
        :return: None
        """
        if is_full_line:
            try:
                self._parse_fun_level(line)
            except ParsingDone:
                pass
        return super(GetFunctionalityLevel, self).on_new_line(line, is_full_line)

    # +CFUN: 0
    _re_fun_level = re.compile(r'^\s*\+CFUN:\s*(?P<fun_level>[\d+]{1,3})\s*$')

    def _parse_fun_level(self, line):
        """
        Parse UE's level of functionality that should look like:

        +CFUN: 1
        """
        if self._regex_helper.match_compiled(self._re_fun_level, line):
            fun_level = self._regex_helper.group("fun_level")
            self.current_ret["functionality_level"] = fun_level
            raise ParsingDone


# -----------------------------------------------------------------------------
# Following documentation is required for library CI.
# It is used to perform command self-test.
#
# Moreover, it documents what will be COMMAND_RESULT when command
# is run with COMMAND_KWARGS on COMMAND_OUTPUT data coming from connection.
#
# When you need to show parsing of multiple outputs just add suffixes:
# COMMAND_OUTPUT_suffix
# COMMAND_KWARGS_suffix
# COMMAND_RESULT_suffix
# -----------------------------------------------------------------------------

COMMAND_OUTPUT_fun_level = """
AT+CFUN?
+CFUN: 1

OK
"""

COMMAND_KWARGS_fun_level = {}

COMMAND_RESULT_fun_level = {'functionality_level': '1'}
