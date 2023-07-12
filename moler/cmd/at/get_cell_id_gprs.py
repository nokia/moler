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
    """
    Command to get gprs cell registration status. Example output:

    +CGREG: <n>,<stat>[,[<lac>],[<ci>],[<AcT>],[<rac>][,[<cause_type>],[<reject_cause>]...
    ...[,[<Active-Time>],[<Periodic-RAU>],[<GPRS-READY-timer>]]]]

    OK
    """
    def __init__(self, connection=None, prompt=None, newline_chars=None, runner=None):
        """Create instance of GetCellIdGprs class"""
        super(GetCellIdGprs, self).__init__(connection, operation='execute', prompt=prompt,
                                            newline_chars=newline_chars, runner=runner)
        self.current_ret = dict()

    def build_command_string(self):
        return "AT+CGREG?"

    def on_new_line(self, line, is_full_line):
        """
        Method to parse command output. Will be called after line with command echo.

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

    # <n>=6,7, where +CREG: <n>,<stat>[,[<lac>],[<ci>],[<AcT>][,<cause_type>,<reject_cause>][,<csg_stat>]
    # +CREG: 6,5,,,,1,2,0
    # +CREG: 7,10,"54DB","0F6B0578",7
    # +CREG: 7,10,"54DB","0F6B0578",7,1,3,0,"abc"
    _re_cell_id_mode_6_7 = \
        re.compile(r'^\s*\+C(G)?REG:\s(?P<n>([0-9]+)),(?P<stat>([0-9]{1,2})),(\")?(?P<lac>([0-9A-Fa-f]*))?(\")?,'
                   r'(\")?(?P<ci>([0-9A-Fa-f]*))?(\")?,(?P<AcT>([0-9]{1,2}))?(,)?(?P<cause_type>([0-9]*))(,)?'
                   r'(?P<reject_cause>([0-9]*))(,)?(?P<csg_stat>([0-9]*))?(,)?(\")?(?P<csginfo>([0-9A-Za-z]*))?(\")?.*$'
                   )

    # <n>=4,5, where +CGREG: <n>,<stat>,[<lac>],[<ci>],[<AcT>],[<rac>][,[<cause_type>],[<reject_cause>],...
    #              ...[<Active-Time>],[<Periodic-RAU>],[<GPRS-READY-timer>]]
    # +CGREG: 4,5,,,,,,,,,
    # +CGREG: 4,5,"54DB","0F6B0578",7,"f0",,,"00100100","01000111","01000011"
    # +CGREG: 5,10,"54DB","0F6B0578",7,"f0",1,3,"00100100","01000111","01000011"
    # +CGREG: 5,10,"54DB","0F6B0578",7,"f0",1,3
    _re_cell_id_mode_4_5 = \
        re.compile(r'^\s*\+CGREG:\s(?P<n>([0-9]+)),(?P<stat>([0-9]{1,2})),(\")?(?P<lac>([0-9A-Fa-f]*))?(\")?,'
                   r'(\")?(?P<ci>([0-9A-Fa-f]*))?(\")?,(?P<AcT>([0-9]{1,2}))?,(\")?(?P<rac>([0-9A-Fa-f]*))?(\")?(,)?'
                   r'(?P<cause_type>([0-9]*))?(,)?(?P<reject_cause>([0-9]*))?(,)?(\")?(?P<Active_Time>([0-9A-Fa-f]*))?'
                   r'(\")?(,)?(\")?(?P<Periodic_RAU>([0-9A-Fa-f]*))?(\")?(,)?(\")?(?P<GPRS_READY_timer>([0-9A-Fa-f]*))?'
                   r'(\")?.*$')

    # <n>=3, where +CGREG: <n>,<stat>,[<lac>],[<ci>],[<AcT>],[<rac>][,<cause_type>,<reject_cause>]
    # +CGREG: 3,5,,,,,1,2
    # +CGREG: 3,5,"54DB","0F6B0578",7,"f0",1,2
    _re_cell_id_mode_3 = \
        re.compile(r'^\s*\+CGREG:\s(?P<n>([0-9]+)),(?P<stat>([0-9]{1,2})),(\")?(?P<lac>([0-9A-Fa-f]*))?(\")?,'
                   r'(\")?(?P<ci>([0-9A-Fa-f]*))?(\")?,(?P<AcT>([0-9]{1,2}))?,(\")?(?P<rac>([0-9A-Fa-f]*))?(\")?(,)?'
                   r'(?P<cause_type>([0-9]+))(,)?(?P<reject_cause>([0-9]+)).*$')

    # <n>=2, where +CGREG: <n>,<stat>,[<lac>],[<ci>],[<AcT>],[<rac>]
    # +CGREG: 2,5,,,,
    # +CGREG: 2,5,"54DB","0F6B0578",7,"f0"
    _re_cell_id_mode_2 = \
        re.compile(r'^\s*\+CGREG:\s(?P<n>([0-9]+)),(?P<stat>([0-9]{1,2})),(\")?(?P<lac>([0-9A-Fa-f]*))?(\")?,'
                   r'(\")?(?P<ci>([0-9A-Fa-f]*))?(\")?,(?P<AcT>([0-9]{1,2}))?,(\")?(?P<rac>([0-9A-Fa-f]*))?(\")?.*$')

    # <n>=0,1, where +CGREG: <n>,<stat>
    # +CGREG: 1,11
    _re_cell_id_mode_0_1 = re.compile(r'^\s*\+C(G)?REG:\s(?P<n>([0-9]+)),(?P<stat>([0-9]{1,2})).*$')

    # +CGREG: <output_data>
    _re_cell_id_data = re.compile(r'^\s*\+C(G)?REG:\s(?P<output_data>\w+\S+).*$')

    def _parse_cell_data_gprs(self, line):
        """
        Parse network registration status and location information:

        +CGREG: 1,11
        or
        +CGREG: 2,5,"54DB","0F6B0578",7,"f0"
        or
        +CGREG: 3,5,"54DB","0F6B0578",7,"f0",1,2
        or
        +CGREG: 5,10,"54DB","0F6B0578",7,"f0",1,3,"00100100","01000111","01000011"
        or
        +CGREG: 7,10,"54DB","0F6B0578",7,1,3,0,"abc"
        """
        def _get_values():
            for key, value in self._regex_helper.groupdict().items():
                self.current_ret[key] = value

        if self._regex_helper.match_compiled(self._re_cell_id_mode_0_1, line):
            _get_values()
            _variant = int(self.current_ret['n'])
            if _variant in (6, 7) and self._regex_helper.match_compiled(self._re_cell_id_mode_6_7, line):
                _get_values()
            elif _variant in (4, 5) and self._regex_helper.match_compiled(self._re_cell_id_mode_4_5, line):
                _get_values()
            elif _variant == 3 and self._regex_helper.match_compiled(self._re_cell_id_mode_3, line):
                _get_values()
            elif _variant == 2 and self._regex_helper.match_compiled(self._re_cell_id_mode_2, line):
                _get_values()
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

COMMAND_OUTPUT_cell_id_gprs_v1 = """
AT+CGREG?
+CGREG: 1,11

OK
"""

COMMAND_KWARGS_cell_id_gprs_v1 = {}

COMMAND_RESULT_cell_id_gprs_v1 = {
    'n': '1',
    'stat': '11',
    'output_data': '1,11'
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
    'output_data': '2,5,"54DB","0F6B0578",7,"f0"'
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
    'lac': '',
    'ci': '',
    'AcT': None,
    'rac': '',
    'output_data': '2,5,,,,'
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
    'output_data': '3,5,"54DB","0F6B0578",15,"f0",1,2'
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
    'lac': '',
    'ci': '',
    'AcT': None,
    'rac': '',
    'cause_type': '1',
    'reject_cause': '2',
    'output_data': '3,5,,,,,1,2'
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
    'lac': '',
    'ci': '',
    'AcT': None,
    'rac': '',
    'cause_type': '',
    'reject_cause': '',
    'Active_Time': '',
    'Periodic_RAU': '',
    'GPRS_READY_timer': '',
    'output_data': '4,5,,,,,,,,,'
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
    'cause_type': '',
    'reject_cause': '',
    'Active_Time': '00100100',
    'Periodic_RAU': '01000111',
    'GPRS_READY_timer': '01000011',
    'output_data': '4,5,"54DB","0F6B0578",7,"f0",,,"00100100","01000111","01000011"'
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
    'output_data': '5,10,"54DB","0F6B0578",7,"f0",1,3,"00100100","01000111","01000011"'
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
    'Active_Time': '',
    'Periodic_RAU': '',
    'GPRS_READY_timer': '',
    'output_data': '5,10,"54DB","0F6B0578",7,"f0",1,3'
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
    'lac': '',
    'ci': '',
    'AcT': None,
    'cause_type': '1',
    'reject_cause': '2',
    'csg_stat': '0',
    'csginfo': '',
    'output_data': '6,5,,,,1,2,0'
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
    'cause_type': '',
    'reject_cause': '',
    'csg_stat': '',
    'csginfo': '',
    'output_data': '7,10,"54DB","0F6B0578",7'
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
    'output_data': '7,10,"54DB","0F6B0578",7,1,3,0,"abc"'
}
