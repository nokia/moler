# -*- coding: utf-8 -*-
"""
AT+CGREG?

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


class GetCellIdGprs(GenericAtCommand):

    def __init__(self, connection=None, prompt=None, newline_chars=None, runner=None):
        """
        Create instance of GetCellIdGprs class and command to get gprs cell registration status.
        Verify with latest 3gpp specification 27.007. Example output:

        +CGREG: <n>,<stat>[,[<lac>],[<ci>],[<AcT>],[<rac>][,[<cause_type>],[<reject_cause>]...
        ...[,[<Active-Time>],[<Periodic-RAU>],[<GPRS-READY-timer>]]]]

        OK

        :param connection: Moler connection to device, terminal when command is executed.
        :param prompt: prompt where we start from.
        :param newline_chars: Characters to split local lines - list.
        :param runner: Runner to run command.
        """
        super(GetCellIdGprs, self).__init__(connection, operation='execute', prompt=prompt,
                                            newline_chars=newline_chars, runner=runner)

    def build_command_string(self):
        return "AT+CGREG?"

    def on_new_line(self, line, is_full_line):
        """
        Method to parse command output. Will be called after line with command echo. Example outputs:

        +CGREG: <n>,<stat>[,[<lac>],[<ci>],[<AcT>],[<rac>][,<cause_type>,<reject_cause>]]

        OK
        or
        +CGREG: <n>,<stat>[,[<lac>],[<ci>],[<AcT>],[<rac>][,[<cause_type>],[<reject_cause>]...
        ...[,[<Active-Time>],[<Periodic-RAU>],[<GPRS-READY-timer>]]]]

        OK

        Write your own implementation but don't forget to call on_new_line from base class

        :param line: Line to parse, new lines are trimmed
        :param is_full_line:  False for chunk of line; True on full line (NOTE: new line character removed)
        :return: None
        """
        if is_full_line:
            try:
                self._parse_cell_data_gprs(line)
            except ParsingDone:
                pass
        return super(GetCellIdGprs, self).on_new_line(line, is_full_line)

    # +C(G)REG: <raw_output> / <n>
    _re_raw_data = re.compile(r'^\s*\+C(G)?REG:\s(?P<raw_output>(?P<n>\d+).*).*$')

    def _parse_cell_data_gprs(self, line):
        """
        Parse network registration status and location information:
        +CGREG: 1,11
        +CGREG: 2,5,,,,
        +CGREG: 2,5,"54DB","0F6B0578",7,"f0"
        +CGREG: 3,5,,,,,1,2
        +CGREG: 3,5,"54DB","0F6B0578",7,"f0",1,2
        +CGREG: 4,5,,,,,,,,,
        +CGREG: 4,5,"54DB","0F6B0578",7,"f0",,,"00100100","01000111","01000011"
        +CGREG: 5,10,"54DB","0F6B0578",7,"f0",1,3,"00100100","01000111","01000011"
        +CGREG: 5,10,"54DB","0F6B0578",7,"f0",1,3
        +CGREG: 5,10,"54DB","0F6B0578",7,"f0",1,3,"00100100","01000111","01000011"
        +CREG: 6,5,,,,1,2,0
        +CREG: 7,10,"54DB","0F6B0578",7
        +CREG: 7,10,"54DB","0F6B0578",7,1,3,0,"abc"
        """
        results_keys = {
            0: ['n', 'stat'],
            1: ['n', 'stat', 'lac', 'ci'],
            2: ['n', 'stat', 'lac', 'ci', 'AcT', 'rac'],
            3: ['n', 'stat', 'lac', 'ci', 'AcT', 'rac', 'cause_type', 'reject_cause'],
            4: ['n', 'stat', 'lac', 'ci', 'AcT', 'rac', 'cause_type', 'reject_cause', 'Active_Time', 'Periodic_RAU',
                'GPRS_READY_timer'],
            5: ['n', 'stat', 'lac', 'ci', 'AcT', 'rac', 'cause_type', 'reject_cause', 'Active_Time', 'Periodic_RAU',
                'GPRS_READY_timer'],
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

COMMAND_OUTPUT_cell_id_gprs_v1 = """
AT+CGREG?
+CGREG: 1,11

OK
"""

COMMAND_KWARGS_cell_id_gprs_v1 = {}

COMMAND_RESULT_cell_id_gprs_v1 = {
    'n': '1',
    'stat': '11',
    'raw_output': '1,11'
}


COMMAND_OUTPUT_cell_id_gprs_v2_1 = """
AT+CGREG?
+CGREG: 2,5,"54DB","0F6B0578",7,"f0"

OK
"""

COMMAND_KWARGS_cell_id_gprs_v2_1 = {}

COMMAND_RESULT_cell_id_gprs_v2_1 = {
    'n': '2',
    'stat': '5',
    'lac': '54DB',
    'ci': '0F6B0578',
    'AcT': '7',
    'rac': 'f0',
    'raw_output': '2,5,"54DB","0F6B0578",7,"f0"'
}

COMMAND_OUTPUT_cell_id_gprs_v2_2 = """
AT+CGREG?
+CGREG: 2,5,,,,

OK
"""

COMMAND_KWARGS_cell_id_gprs_v2_2 = {}

COMMAND_RESULT_cell_id_gprs_v2_2 = {
    'n': '2',
    'stat': '5',
    'raw_output': '2,5,,,,'
}

COMMAND_OUTPUT_cell_id_gprs_v3_1 = """
AT+CGREG?
+CGREG: 3,5,"54DB","0F6B0578",15,"f0",1,2

OK
"""

COMMAND_KWARGS_cell_id_gprs_v3_1 = {}

COMMAND_RESULT_cell_id_gprs_v3_1 = {
    'n': '3',
    'stat': '5',
    'lac': '54DB',
    'ci': '0F6B0578',
    'AcT': '15',
    'rac': 'f0',
    'cause_type': '1',
    'reject_cause': '2',
    'raw_output': '3,5,"54DB","0F6B0578",15,"f0",1,2'
}

COMMAND_OUTPUT_cell_id_gprs_v3_2 = """
AT+CGREG?
+CGREG: 3,5,,,,,1,2

OK
"""

COMMAND_KWARGS_cell_id_gprs_v3_2 = {}

COMMAND_RESULT_cell_id_gprs_v3_2 = {
    'n': '3',
    'stat': '5',
    'cause_type': '1',
    'reject_cause': '2',
    'raw_output': '3,5,,,,,1,2'
}

COMMAND_OUTPUT_cell_id_gprs_v45_1 = """
AT+CGREG?
+CGREG: 4,5,,,,,,,,,

OK
"""

COMMAND_KWARGS_cell_id_gprs_v45_1 = {}

COMMAND_RESULT_cell_id_gprs_v45_1 = {
    'n': '4',
    'stat': '5',
    'raw_output': '4,5,,,,,,,,,'
}

COMMAND_OUTPUT_cell_id_gprs_v45_2 = """
AT+CGREG?
+CGREG: 4,5,"54DB","0F6B0578",7,"f0",,,"00100100","01000111","01000011"

OK
"""

COMMAND_KWARGS_cell_id_gprs_v45_2 = {}

COMMAND_RESULT_cell_id_gprs_v45_2 = {
    'n': '4',
    'stat': '5',
    'lac': '54DB',
    'ci': '0F6B0578',
    'AcT': '7',
    'rac': 'f0',
    'Active_Time': '00100100',
    'Periodic_RAU': '01000111',
    'GPRS_READY_timer': '01000011',
    'raw_output': '4,5,"54DB","0F6B0578",7,"f0",,,"00100100","01000111","01000011"'
}

COMMAND_OUTPUT_cell_id_gprs_v45_3 = """
AT+CGREG?
+CGREG: 5,10,"54DB","0F6B0578",7,"f0",1,3,"00100100","01000111","01000011"

OK
"""

COMMAND_KWARGS_cell_id_gprs_v45_3 = {}

COMMAND_RESULT_cell_id_gprs_v45_3 = {
    'n': '5',
    'stat': '10',
    'lac': '54DB',
    'ci': '0F6B0578',
    'AcT': '7',
    'rac': 'f0',
    'cause_type': '1',
    'reject_cause': '3',
    'Active_Time': '00100100',
    'Periodic_RAU': '01000111',
    'GPRS_READY_timer': '01000011',
    'raw_output': '5,10,"54DB","0F6B0578",7,"f0",1,3,"00100100","01000111","01000011"'
}

COMMAND_OUTPUT_cell_id_gprs_v45_4 = """
AT+CGREG?
+CGREG: 5,10,"54DB","0F6B0578",7,"f0",1,3

OK
"""

COMMAND_KWARGS_cell_id_gprs_v45_4 = {}

COMMAND_RESULT_cell_id_gprs_v45_4 = {
    'n': '5',
    'stat': '10',
    'lac': '54DB',
    'ci': '0F6B0578',
    'AcT': '7',
    'rac': 'f0',
    'cause_type': '1',
    'reject_cause': '3',
    'raw_output': '5,10,"54DB","0F6B0578",7,"f0",1,3'
}

COMMAND_OUTPUT_cell_id_gprs_v67_1 = """
AT+CGREG?
+CREG: 6,5,,,,1,2,0

OK
"""

COMMAND_KWARGS_cell_id_gprs_v67_1 = {}

COMMAND_RESULT_cell_id_gprs_v67_1 = {
    'n': '6',
    'stat': '5',
    'cause_type': '1',
    'reject_cause': '2',
    'csg_stat': '0',
    'raw_output': '6,5,,,,1,2,0'
}

COMMAND_OUTPUT_cell_id_gprs_v67_2 = """
AT+CGREG?
+CREG: 7,10,"54DB","0F6B0578",7

OK
"""

COMMAND_KWARGS_cell_id_gprs_v67_2 = {}

COMMAND_RESULT_cell_id_gprs_v67_2 = {
    'n': '7',
    'stat': '10',
    'lac': '54DB',
    'ci': '0F6B0578',
    'AcT': '7',
    'raw_output': '7,10,"54DB","0F6B0578",7'
}

COMMAND_OUTPUT_cell_id_gprs_v67_3 = """
AT+CGREG?
+CREG: 7,10,"54DB","0F6B0578",7,1,3,0,"abc"

OK
"""

COMMAND_KWARGS_cell_id_gprs_v67_3 = {}

COMMAND_RESULT_cell_id_gprs_v67_3 = {
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
