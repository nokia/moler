# -*- coding: utf-8 -*-
"""
AT+CIMI .

AT commands specification:
google for: 3gpp specification 27.007
(always check against latest version of standard)
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import re

from moler.cmd.at.genericat import GenericAtCommand
from moler.exceptions import ParsingDone


class GetImsi(GenericAtCommand):
    """
    Command to get IMSI. Example output:

    AT+CIMI
    49009123123123
    OK
    """
    def __init__(self, connection=None, prompt=None, newline_chars=None, runner=None):
        """Create instance of GetImsi class"""
        super(GetImsi, self).__init__(connection, operation='execute', prompt=prompt,
                                      newline_chars=newline_chars, runner=runner)

    def build_command_string(self):
        return "AT+CIMI"

    def on_new_line(self, line, is_full_line):
        """
        Method to parse command output. Will be called after line with command echo.

        49009123123123
        OK

        Write your own implementation but don't forget to call on_new_line from base class

        :param line: Line to parse, new lines are trimmed
        :param is_full_line:  False for chunk of line; True on full line (NOTE: new line character removed)
        :return: None
        """
        if is_full_line:
            try:
                self._parse_imsi_number(line)
            except ParsingDone:
                pass
        return super(GetImsi, self).on_new_line(line, is_full_line)

    _re_imsi = re.compile(r'^\s*(?P<imsi>\d+)\s*$')

    def _parse_imsi_number(self, line):
        """
        Parse IMSI number that should look like:

        49009123123123
        """
        if self._regex_helper.match_compiled(self._re_imsi, line):
            imsi = self._regex_helper.group("imsi")
            self.current_ret['imsi'] = imsi
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

COMMAND_OUTPUT_ver_execute = """
AT+CIMI
440801200189934
OK
"""

COMMAND_KWARGS_ver_execute = {}

COMMAND_RESULT_ver_execute = {
    'imsi': '440801200189934'
}
