# -*- coding: utf-8 -*-
"""
AT+CREG?

AT commands specification:
google for: 3gpp specification 27.007
(always check against latest version of standard)
"""

__author__ = 'Jakub Kochaniak'
__copyright__ = 'Copyright (C) 2023, Nokia'
__email__ = 'jakub.kochaniak@nokia.com'

import re

from moler.cmd.at.genericat import GenericAtCommand
from moler.exceptions import ParsingDone


class GetCellId(GenericAtCommand):
    """
    Command to get cell registration status. Example output:

    +CREG: <n>,<stat>[,[<lac>],[<ci>],[<AcT>][,<cause_type>,<reject_cause>]]

    OK
    """
    def __init__(self, connection=None, prompt=None, newline_chars=None, runner=None):
        """Create instance of GetCellIdGsm class"""
        super(GetCellId, self).__init__(connection, operation='execute', prompt=prompt,
                                        newline_chars=newline_chars, runner=runner)
        self.current_ret = dict()

    def build_command_string(self):
        return "AT+CREG?"

    def on_new_line(self, line, is_full_line):
        """
        Method to parse command output. Will be called after line with command echo.

        +CREG: <n>,<stat>[,[<lac>],[<ci>],[<AcT>][,<cause_type>,<reject_cause>]]

        OK

        Write your own implementation but don't forget to call on_new_line from base class

        :param line: Line to parse, new lines are trimmed
        :param is_full_line:  False for chunk of line; True on full line (NOTE: new line character removed)
        :return: None
        """
        if is_full_line:
            try:
                self._parse_cell_data(line)
            except ParsingDone:
                pass
        return super(GetCellId, self).on_new_line(line, is_full_line)

    # <n>=3, where +CREG: <n>,<stat>,[<lac>],[<ci>],[<AcT>],<cause_type>,<reject_cause>
    # +CREG: 3,5,,,,1,2
    # +CREG: 3,5,"54DB","0F6B0578",15,1,2
    _re_network_reg_mode_3 = \
        re.compile(r'^\s*\+CREG:\s(?P<n>([0-9]+)),(?P<stat>([0-9]{1,2})),(\")?(?P<lac>([0-9A-Fa-f]*))?(\")?,'
                   r'(\")?(?P<ci>([0-9A-Fa-f]*))?(\")?,(?P<AcT>([0-9]{1,2}))?,(?P<cause_type>([0-9]+)),'
                   r'(?P<reject_cause>([0-9]+)).*$')

    # <n>=2, where +CREG: <n>,<stat>,[<lac>],[<ci>],[<AcT>]
    # +CREG: 2,5,,,
    # +CREG: 2,5,"54DB","0F6B0578",7
    _re_network_reg_mode_2 = \
        re.compile(r'^\s*\+CREG:\s(?P<n>([0-9]+)),(?P<stat>([0-9]{1,2})),(\")?(?P<lac>([0-9A-Fa-f]*))?(\")?,'
                   r'(\")?(?P<ci>([0-9A-Fa-f]*))?(\")?,(?P<AcT>([0-9]{1,2}))?.*$')

    # <n>=0,1, where +CREG: <n>,<stat>
    # +CREG: 1,1
    _re_network_reg_mode_0_1 = re.compile(r'^\s*\+CREG:\s(?P<n>([0-9]+)),(?P<stat>([0-9]{1,2})).*$')

    # +CREG: <output_data>
    _re_cell_id_data = re.compile(r'^\s*\+CREG:\s(?P<output_data>\w+\S+).*$')

    def _parse_cell_data(self, line):
        """
        Parse network registration status and location information:

        +CREG: 1,1
        or
        +CREG: 2,5,,,
        or
        +CREG: 2,5,"54DB","0F6B0578",7
        or
        +CREG: 3,5,,,,1,2
        or
        +CREG: 2,5,"54DB","0F6B0578",15,1,2
        """
        if self._regex_helper.match_compiled(self._re_network_reg_mode_3, line):
            for key, value in self._regex_helper.groupdict().items():
                self.current_ret[key] = value
        elif self._regex_helper.match_compiled(self._re_network_reg_mode_2, line):
            for key, value in self._regex_helper.groupdict().items():
                self.current_ret[key] = value
        elif self._regex_helper.match_compiled(self._re_network_reg_mode_0_1, line):
            for key, value in self._regex_helper.groupdict().items():
                self.current_ret[key] = value
        if self._regex_helper.match_compiled(self._re_cell_id_data, line):
            self.current_ret['output_data'] = self._regex_helper.groupdict().get('output_data')
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

COMMAND_OUTPUT_cell_id_v1 = """
AT+CREG?
+CREG: 1,1

OK
"""

COMMAND_KWARGS_cell_id_v1 = {}

COMMAND_RESULT_cell_id_v1 = {
    'n': '1',
    'stat': '1',
    'output_data': '1,1'
}

COMMAND_OUTPUT_cell_id_v2_1 = """
AT+CREG?
+CREG: 2,5,"54DB","0F6B0578",7

OK
"""

COMMAND_KWARGS_cell_id_v2_1 = {}

COMMAND_RESULT_cell_id_v2_1 = {
    'n': '2',
    'stat': '5',
    'lac': '54DB',
    'ci': '0F6B0578',
    'AcT': '7',
    'output_data': '2,5,"54DB","0F6B0578",7'
}

COMMAND_OUTPUT_cell_id_v2_2 = """
AT+CREG?
+CREG: 2,5,,,

OK
"""

COMMAND_KWARGS_cell_id_v2_2 = {}

COMMAND_RESULT_cell_id_v2_2 = {
    'n': '2',
    'stat': '5',
    'lac': '',
    'ci': '',
    'AcT': None,
    'output_data': '2,5,,,'
}

COMMAND_OUTPUT_cell_id_v3_1 = """
AT+CREG?
+CREG: 3,5,"54DB","0F6B0578",15,1,2

OK
"""

COMMAND_KWARGS_cell_id_v3_1 = {}

COMMAND_RESULT_cell_id_v3_1 = {
    'n': '3',
    'stat': '5',
    'lac': '54DB',
    'ci': '0F6B0578',
    'AcT': '15',
    'cause_type': '1',
    'reject_cause': '2',
    'output_data': '3,5,"54DB","0F6B0578",15,1,2'
}

COMMAND_OUTPUT_cell_id_v3_2 = """
AT+CREG?
+CREG: 3,5,,,15,1,2

OK
"""

COMMAND_KWARGS_cell_id_v3_2 = {}

COMMAND_RESULT_cell_id_v3_2 = {
    'n': '3',
    'stat': '5',
    'lac': '',
    'ci': '',
    'AcT': '15',
    'cause_type': '1',
    'reject_cause': '2',
    'output_data': '3,5,,,15,1,2'
}
