# -*- coding: utf-8 -*-
"""
AT+C5GREG?

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


class GetCellIdNr(GenericAtCommand):

    def __init__(self, connection=None, prompt=None, newline_chars=None, runner=None):
        """
        Create instance of GetCellIdNr class and command to get NR cell registration status.
        Verify with latest 3gpp specification 27.007. Example output:

        +C5GREG: <n>,<stat>[,[<lac>],[<ci>],[<AcT>],[<Allowed_NSSAI_length>], [<Allowed_NSSAI>][,[<cause_type>],
        [<reject_cause>]][,[<cag_stat>][,<caginfo>]

        OK

        where <n> Possible options for selected_mode, but verify with latest 3gpp specification 27.007.

        :param connection: Moler connection to device, terminal when command is executed.
        :param prompt: prompt where we start from.
        :param newline_chars: Characters to split local lines - list.
        :param runner: Runner to run command.
        """
        super(GetCellIdNr, self).__init__(connection, operation='execute', prompt=prompt,
                                          newline_chars=newline_chars, runner=runner)

    def build_command_string(self):
        return "AT+C5GREG?"

    def on_new_line(self, line, is_full_line):
        """
        Method to parse command output. Will be called after line with command echo.

        +C5GREG: <n>,<stat>[,[<tac>],[<ci>],[<AcT>],[<Allowed_NSSAI_length>],[<Allowed_NSSAI>]...
                 ...[,<cause_type>,<reject_cause>]][,<cag_stat>][,<caginfo>]

        OK

        Write your own implementation but don't forget to call on_new_line from base class

        :param line: Line to parse, new lines are trimmed
        :param is_full_line:  False for chunk of line; True on full line (NOTE: new line character removed)
        :return: None
        """
        if is_full_line:
            try:
                self._parse_cell_data_nr(line)
            except ParsingDone:
                pass
        return super(GetCellIdNr, self).on_new_line(line, is_full_line)

    # +C5GREG: <raw_output>
    _re_raw_data = re.compile(r'^\s*\+C5GREG:\s(?P<raw_output>.*).*$')

    def _parse_cell_data_nr(self, line):
        """
        Parse network registration status and location information:
        +C5GREG: 1,11
        +C5GREG: 1,"54DB","0F6B0578",7,2,"aB"
        +C5GREG: 2,5,"54DB","0F6B0578",7,2,"aB"
        +C5GREG: 3,5,,,,,,1,2
        +C5GREG: 3,5,"54DB","0F6B0578",7,2,"aB",1,2
        +C5GREG: 4,5,,,,,,1,2
        +C5GREG: 5,5,"54DB","0F6B0578",7,2,"aB",1,2,123,"info"
        """
        results_keys = \
            ['n', 'stat', 'tac', 'ci', 'AcT', 'Allowed_NSSAI_length', 'Allowed_NSSAI', 'cause_type', 'reject_cause',
             'cag_stat', 'caginfo']
        if self._regex_helper.match_compiled(self._re_raw_data, line):
            string_raw_output = self._regex_helper.groupdict().get('raw_output')
            self.current_ret['raw_output'] = string_raw_output
            list_output = string_raw_output.split(',')
            # Case without <stat> in output pop this value from result keys:
            if "\"" in list_output[1]:
                del (results_keys[1])
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

COMMAND_OUTPUT_cell_id_nr_v1_1 = """
AT+C5GREG?
+C5GREG: 1,11

OK
"""

COMMAND_KWARGS_cell_id_nr_v1_1 = {}

COMMAND_RESULT_cell_id_nr_v1_1 = {
    'n': '1',
    'stat': '11',
    'raw_output': '1,11'
}

COMMAND_OUTPUT_cell_id_nr_v1_2 = """
AT+C5GREG?
+C5GREG: 1,"1964","260768000",11,4,"01.D143A5"

OK
"""

COMMAND_KWARGS_cell_id_nr_v1_2 = {}

COMMAND_RESULT_cell_id_nr_v1_2 = {
    'n': '1',
    'tac': '1964',
    'ci': '260768000',
    'AcT': '11',
    'Allowed_NSSAI_length': '4',
    'Allowed_NSSAI': '01.D143A5',
    'raw_output': '1,"1964","260768000",11,4,"01.D143A5"'
}

COMMAND_OUTPUT_cell_id_nr_v2_1 = """
AT+C5GREG?
+C5GREG: 2,5,"54DB","0F6B0578",7,2,"aB"

OK
"""

COMMAND_KWARGS_cell_id_nr_v2_1 = {}

COMMAND_RESULT_cell_id_nr_v2_1 = {
    'n': '2',
    'stat': '5',
    'tac': '54DB',
    'ci': '0F6B0578',
    'AcT': '7',
    'Allowed_NSSAI_length': '2',
    'Allowed_NSSAI': 'aB',
    'raw_output': '2,5,"54DB","0F6B0578",7,2,"aB"'
}

COMMAND_OUTPUT_cell_id_nr_v2_2 = """
AT+C5GREG?
+C5GREG: 2,5,,,,,

OK
"""

COMMAND_KWARGS_cell_id_nr_v2_2 = {}

COMMAND_RESULT_cell_id_nr_v2_2 = {
    'n': '2',
    'stat': '5',
    'raw_output': '2,5,,,,,'
}

COMMAND_OUTPUT_cell_id_nr_v3_1 = """
AT+C5GREG?
+C5GREG: 3,5,"54DB","0F6B0578",7,2,"aB",1,2

OK
"""

COMMAND_KWARGS_cell_id_nr_v3_1 = {}

COMMAND_RESULT_cell_id_nr_v3_1 = {
    'n': '3',
    'stat': '5',
    'tac': '54DB',
    'ci': '0F6B0578',
    'AcT': '7',
    'Allowed_NSSAI_length': '2',
    'Allowed_NSSAI': 'aB',
    'cause_type': '1',
    'reject_cause': '2',
    'raw_output': '3,5,"54DB","0F6B0578",7,2,"aB",1,2'
}

COMMAND_OUTPUT_cell_id_nr_v3_2 = """
AT+C5GREG?
+C5GREG: 3,5,,,,,,1,2

OK
"""

COMMAND_KWARGS_cell_id_nr_v3_2 = {}

COMMAND_RESULT_cell_id_nr_v3_2 = {
    'n': '3',
    'stat': '5',
    'cause_type': '1',
    'reject_cause': '2',
    'raw_output': '3,5,,,,,,1,2'
}

COMMAND_OUTPUT_cell_id_nr_v45_1 = """
AT+C5GREG?
+C5GREG: 4,5,,,,,,1,2

OK
"""

COMMAND_KWARGS_cell_id_nr_v45_1 = {}

COMMAND_RESULT_cell_id_nr_v45_1 = {
    'n': '4',
    'stat': '5',
    'cause_type': '1',
    'reject_cause': '2',
    'raw_output': '4,5,,,,,,1,2'
}

COMMAND_OUTPUT_cell_id_nr_v45_2 = """
AT+C5GREG?
+C5GREG: 5,5,"54DB","0F6B0578",7,2,"aB",1,2,123,"info"

OK
"""

COMMAND_KWARGS_cell_id_nr_v45_2 = {}

COMMAND_RESULT_cell_id_nr_v45_2 = {
    'n': '5',
    'stat': '5',
    'tac': '54DB',
    'ci': '0F6B0578',
    'AcT': '7',
    'Allowed_NSSAI_length': '2',
    'Allowed_NSSAI': 'aB',
    'cause_type': '1',
    'reject_cause': '2',
    'cag_stat': '123',
    'caginfo': 'info',
    'raw_output': '5,5,"54DB","0F6B0578",7,2,"aB",1,2,123,"info"'
}
