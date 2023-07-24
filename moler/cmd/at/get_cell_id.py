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

    def __init__(self, connection=None, prompt=None, newline_chars=None, runner=None):
        """
        Create instance of GetCellIdGsm class and command to get cell registration status.
        Verify with latest 3gpp specification 27.007. Example output:

        +CREG: <n>,<stat>[,[<lac>],[<ci>],[<AcT>][,<cause_type>,<reject_cause>]]

        OK

        :param connection: Moler connection to device, terminal when command is executed.
        :param prompt: prompt where we start from.
        :param newline_chars: Characters to split local lines - list.
        :param runner: Runner to run command.
        """
        super(GetCellId, self).__init__(connection, operation='execute', prompt=prompt,
                                        newline_chars=newline_chars, runner=runner)

    def build_command_string(self):
        return "AT+CREG?"

    def on_new_line(self, line, is_full_line):
        """
        Method to parse command output. Will be called after line with command echo. Example output:

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

    # +CREG: <raw_output>
    _re_raw_data = re.compile(r'^\s*\+CREG:\s(?P<raw_output>.*).*$')

    def _parse_cell_data(self, line):
        """
        Parse network registration status and location information:
        +CREG: 1,1
        +CREG: 2,5,,,
        +CREG: 2,5,"54DB","0F6B0578",7
        +CREG: 3,5,,,,1,2
        +CREG: 3,5,"54DB","0F6B0578",15,1,2
        """
        results_keys = ['n', 'stat', 'lac', 'ci', 'AcT', 'cause_type', 'reject_cause']
        if self._regex_helper.match_compiled(self._re_raw_data, line):
            string_raw_output = self._regex_helper.groupdict().get('raw_output')
            self.current_ret['raw_output'] = string_raw_output
            list_output = string_raw_output.split(',')
            for index, item in enumerate(list_output, 0):
                if item:
                    self.current_ret[results_keys[index]] = item.strip('"')
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
    'raw_output': '1,1'
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
    'raw_output': '2,5,"54DB","0F6B0578",7'
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
    'raw_output': '2,5,,,'
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
    'raw_output': '3,5,"54DB","0F6B0578",15,1,2'
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
    'AcT': '15',
    'cause_type': '1',
    'reject_cause': '2',
    'raw_output': '3,5,,,15,1,2'
}
