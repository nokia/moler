# -*- coding: utf-8 -*-
"""
AT+CEREG?

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


class GetCellIdLte(GenericAtCommand):

    def __init__(self, connection=None, prompt=None, newline_chars=None, runner=None):
        """
        Create instance of GetCellIdLte class and command to get LTE cell registration status.
        Verify with latest 3gpp specification 27.007. Example output:

        +CEREG: <n>,<stat>[,[<lac>],[<ci>],[<AcT>][,[<cause_type>],[<reject_cause>]
        [,[<Active-Time>],[<Periodic-RAU>],[<GPRS-READY-timer>]]]]

        OK

        :param connection: Moler connection to device, terminal when command is executed.
        :param prompt: prompt where we start from.
        :param newline_chars: Characters to split local lines - list.
        :param runner: Runner to run command.
        """
        super(GetCellIdLte, self).__init__(connection, operation='execute', prompt=prompt,
                                           newline_chars=newline_chars, runner=runner)

    def build_command_string(self):
        return "AT+CEREG?"

    def on_new_line(self, line, is_full_line):
        """
        Method to parse command output. Will be called after line with command echo.

        +CEREG: <n>,<stat>[,[<lac>],[<ci>],[<AcT>][,<cause_type>,<reject_cause>]]

        OK
        or
        +CEREG: <n>,<stat>[,[<lac>],[<ci>],[<AcT>][,[<cause_type>],[<reject_cause>]...
        ...[,[<Active-Time>],[<Periodic-RAU>],[<GPRS-READY-timer>]]]]

        OK

        Write your own implementation but don't forget to call on_new_line from base class

        :param line: Line to parse, new lines are trimmed
        :param is_full_line:  False for chunk of line; True on full line (NOTE: new line character removed)
        :return: None
        """
        if is_full_line:
            try:
                self._parse_cell_data_lte(line)
            except ParsingDone:
                pass
        return super(GetCellIdLte, self).on_new_line(line, is_full_line)

    # +C(E)REG: <raw_output> / <n>
    _re_raw_data = re.compile(r'^\s*\+C(E)?REG:\s(?P<raw_output>(?P<n>\d+).*).*$')

    def _parse_cell_data_lte(self, line):
        """
        Parse network registration status and location information:
        +CEREG: 1,11
        +CEREG: 2,5,,,
        +CEREG: 2,5,"54DB","0F6B0578",7
        +CEREG: 3,5,,,,1,2
        +CEREG: 3,5,"54DB","0F6B0578",7,1,2
        +CEREG: 4,5,,,,,,,
        +CEREG: 4,5,"54DB","0F6B0578",7,,,"00100100","01000111"
        +CEREG: 5,10,"54DB","0F6B0578",7,1,3,"00100100","01000111"
        +CEREG: 5,10,"54DB","0F6B0578",7,1,3
        +CEREG: 5,10,"54DB","0F6B0578",7,1,3,"00100100","01000111"
        +CREG: 6,5,,,,1,2,0
        +CREG: 7,10,"54DB","0F6B0578",7
        +CREG: 7,10,"54DB","0F6B0578",7,1,3,0,"abc"
        """
        results_keys = {
            0: ['n', 'stat'],
            1: ['n', 'stat', 'tac', 'ci'],
            2: ['n', 'stat', 'tac', 'ci', 'AcT'],
            3: ['n', 'stat', 'tac', 'ci', 'AcT', 'cause_type', 'reject_cause'],
            4: ['n', 'stat', 'tac', 'ci', 'AcT', 'cause_type', 'reject_cause', 'Active_Time', 'Periodic_RAU'],
            5: ['n', 'stat', 'tac', 'ci', 'AcT', 'cause_type', 'reject_cause', 'Active_Time', 'Periodic_RAU'],
            6: ['n', 'stat', 'lac', 'ci', 'AcT', 'cause_type', 'reject_cause', 'csg_stat'],
            7: ['n', 'stat', 'lac', 'ci', 'AcT', 'cause_type', 'reject_cause', 'csg_stat', 'csginfo'],
        }
        if self._regex_helper.match_compiled(self._re_raw_data, line):
            _variant = int(self._regex_helper.groupdict().get('n'))
            string_raw_output = self._regex_helper.groupdict().get('raw_output')
            self.current_ret['raw_output'] = string_raw_output
            list_output = string_raw_output.split(',')
            for index, item in enumerate(list_output, 0):
                if item:
                    self.current_ret[results_keys[_variant][index]] = item.strip('"')
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
COMMAND_OUTPUT_cell_id_lte_v1 = """
AT+CEREG?
+CEREG: 1,11

OK
"""

COMMAND_KWARGS_cell_id_lte_v1 = {}

COMMAND_RESULT_cell_id_lte_v1 = {
    'n': '1',
    'stat': '11',
    'raw_output': '1,11'
}

COMMAND_OUTPUT_cell_id_lte_v2_1 = """
AT+CEREG?
+CEREG: 2,5,"54DB","0F6B0578",7

OK
"""

COMMAND_KWARGS_cell_id_lte_v2_1 = {}

COMMAND_RESULT_cell_id_lte_v2_1 = {
    'n': '2',
    'stat': '5',
    'tac': '54DB',
    'ci': '0F6B0578',
    'AcT': '7',
    'raw_output': '2,5,"54DB","0F6B0578",7'
}

COMMAND_OUTPUT_cell_id_lte_v2_2 = """
AT+CEREG?
+CEREG: 2,5,,,

OK
"""

COMMAND_KWARGS_cell_id_lte_v2_2 = {}

COMMAND_RESULT_cell_id_lte_v2_2 = {
    'n': '2',
    'stat': '5',
    'raw_output': '2,5,,,'
}

COMMAND_OUTPUT_cell_id_lte_v3_1 = """
AT+CEREG?
+CEREG: 3,5,"54DB","0F6B0578",15,1,2

OK
"""

COMMAND_KWARGS_cell_id_lte_v3_1 = {}

COMMAND_RESULT_cell_id_lte_v3_1 = {
    'n': '3',
    'stat': '5',
    'tac': '54DB',
    'ci': '0F6B0578',
    'AcT': '15',
    'cause_type': '1',
    'reject_cause': '2',
    'raw_output': '3,5,"54DB","0F6B0578",15,1,2'
}

COMMAND_OUTPUT_cell_id_lte_v3_2 = """
AT+CEREG?
+CEREG: 3,5,,,,1,2

OK
"""

COMMAND_KWARGS_cell_id_lte_v3_2 = {}

COMMAND_RESULT_cell_id_lte_v3_2 = {
    'n': '3',
    'stat': '5',
    'cause_type': '1',
    'reject_cause': '2',
    'raw_output': '3,5,,,,1,2'
}

COMMAND_OUTPUT_cell_id_lte_v45_1 = """
AT+CEREG?
+CEREG: 4,5,,,,,,,

OK
"""

COMMAND_KWARGS_cell_id_lte_v45_1 = {}

COMMAND_RESULT_cell_id_lte_v45_1 = {
    'n': '4',
    'stat': '5',
    'raw_output': '4,5,,,,,,,'
}

COMMAND_OUTPUT_cell_id_lte_v45_2 = """
AT+CEREG?
+CEREG: 4,5,"54DB","0F6B0578",7,,,"00100100","01000111"

OK
"""

COMMAND_KWARGS_cell_id_lte_v45_2 = {}

COMMAND_RESULT_cell_id_lte_v45_2 = {
    'n': '4',
    'stat': '5',
    'tac': '54DB',
    'ci': '0F6B0578',
    'AcT': '7',
    'Active_Time': '00100100',
    'Periodic_RAU': '01000111',
    'raw_output': '4,5,"54DB","0F6B0578",7,,,"00100100","01000111"'
}

COMMAND_OUTPUT_cell_id_lte_v45_3 = """
AT+CEREG?
+CEREG: 5,10,"54DB","0F6B0578",7,1,3,"00100100","01000111"

OK
"""

COMMAND_KWARGS_cell_id_lte_v45_3 = {}

COMMAND_RESULT_cell_id_lte_v45_3 = {
    'n': '5',
    'stat': '10',
    'tac': '54DB',
    'ci': '0F6B0578',
    'AcT': '7',
    'cause_type': '1',
    'reject_cause': '3',
    'Active_Time': '00100100',
    'Periodic_RAU': '01000111',
    'raw_output': '5,10,"54DB","0F6B0578",7,1,3,"00100100","01000111"'
}

COMMAND_OUTPUT_cell_id_lte_v45_4 = """
AT+CEREG?
+CEREG: 5,10,"54DB","0F6B0578",7,1,3

OK
"""

COMMAND_KWARGS_cell_id_lte_v45_4 = {}

COMMAND_RESULT_cell_id_lte_v45_4 = {
    'n': '5',
    'stat': '10',
    'tac': '54DB',
    'ci': '0F6B0578',
    'AcT': '7',
    'cause_type': '1',
    'reject_cause': '3',
    'raw_output': '5,10,"54DB","0F6B0578",7,1,3'
}

COMMAND_OUTPUT_cell_id_lte_v6_1 = """
AT+CEREG?
+CREG: 6,5,,,,1,2,0

OK
"""

COMMAND_KWARGS_cell_id_lte_v6_1 = {}

COMMAND_RESULT_cell_id_lte_v6_1 = {
    'n': '6',
    'stat': '5',
    'cause_type': '1',
    'reject_cause': '2',
    'csg_stat': '0',
    'raw_output': '6,5,,,,1,2,0'
}

COMMAND_OUTPUT_cell_id_lte_v7_1 = """
AT+CEREG?
+CREG: 7,10,"54DB","0F6B0578",7

OK
"""

COMMAND_KWARGS_cell_id_lte_v7_1 = {}

COMMAND_RESULT_cell_id_lte_v7_1 = {
    'n': '7',
    'stat': '10',
    'lac': '54DB',
    'ci': '0F6B0578',
    'AcT': '7',
    'raw_output': '7,10,"54DB","0F6B0578",7'
}

COMMAND_OUTPUT_cell_id_lte_v7_2 = """
AT+CEREG?
+CREG: 7,10,"54DB","0F6B0578",7,1,3,0,"abc"

OK
"""

COMMAND_KWARGS_cell_id_lte_v7_2 = {}

COMMAND_RESULT_cell_id_lte_v7_2 = {
    'n': '7',
    'stat': '10',
    'lac': '54DB',
    'ci': '0F6B0578',
    'AcT': '7',
    'cause_type': '1',
    'reject_cause': '3',
    'csg_stat': '0',
    'csginfo': 'abc',
    'raw_output': '7,10,"54DB","0F6B0578",7,1,3,0,"abc"'
}
