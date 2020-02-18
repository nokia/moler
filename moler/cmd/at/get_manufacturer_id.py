# -*- coding: utf-8 -*-
"""
AT+CGMI .

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


class GetManufacturerId(GenericAtCommand):
    """
    Command to get manufacturer identification. Example output:

    AT+CGMI
    QUALCOMM INCORPORATED
    """
    def __init__(self, connection=None, prompt=None, newline_chars=None, runner=None):
        """Create instance of GetManufacturerId class"""
        super(GetManufacturerId, self).__init__(connection, operation='execute', prompt=prompt,
                                                newline_chars=newline_chars, runner=runner)

    def build_command_string(self):
        return "AT+CGMI"

    def on_new_line(self, line, is_full_line):
        """
        Method to parse command output. Will be called after line with command echo.

        QUALCOMM INCORPORATED

        Write your own implementation but don't forget to call on_new_line from base class

        :param line: Line to parse, new lines are trimmed
        :param is_full_line:  False for chunk of line; True on full line (NOTE: new line character removed)
        :return: None
        """
        if is_full_line:
            try:
                self._parse_manufacturer(line)
            except ParsingDone:
                pass
        return super(GetManufacturerId, self).on_new_line(line, is_full_line)

    _re_manufacturer = re.compile(r'^\s*(?P<manufacturer>\S.*)\s*$')

    def _parse_manufacturer(self, line):
        """
        Parse manufacturer identification that may look like:

        QUALCOMM INCORPORATED
        """
        if self._regex_helper.match_compiled(self._re_manufacturer, line):
            manufacturer = self._regex_helper.group("manufacturer")
            self.current_ret['manufacturer'] = manufacturer
            raise ParsingDone

    def is_end_of_cmd_output(self, line):
        """
        Checks if end of command is reached.

        AT+CGMI is not finished by OK, so it is finished when it detects manufacturer

        :param line: Line from device.
        :return:
        """
        return 'manufacturer' in self.current_ret


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
AT+CGMI
QUALCOMM INCORPORATED
"""

COMMAND_KWARGS_ver_execute = {}

COMMAND_RESULT_ver_execute = {
    'manufacturer': 'QUALCOMM INCORPORATED'
}
