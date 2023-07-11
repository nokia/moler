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
    """
    Command to get cell registration status. Example output:

    +CEREG: <n>,<stat>[,[<lac>],[<ci>],[<AcT>][,<cause_type>,<reject_cause>]]

    OK
    or
    +CEREG: <n>,<stat>[,[<lac>],[<ci>],[<AcT>][,[<cause_type>],[<reject_cause>]...
    ...[,[<Active-Time>],[<Periodic-RAU>],[<GPRS-READY-timer>]]]]

    OK
    """
    def __init__(self, connection=None, prompt=None, newline_chars=None, runner=None):
        """Create instance of GetCellIdGsm class"""
        super(GetCellIdLte, self).__init__(connection, operation='execute', prompt=prompt,
                                           newline_chars=newline_chars, runner=runner)
        self.current_ret = {}

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
                self._parse_ip(line)
            except ParsingDone:
                pass
        return super(GetCellIdLte, self).on_new_line(line, is_full_line)

    # <n>=6,7, where +CREG: <n>,<stat>[,[<lac>],[<ci>],[<AcT>][,<cause_type>,<reject_cause>][,<csg_stat>]
    # +CREG: 6,5,,,,1,2,0
    # +CREG: 7,10,"54DB","0F6B0578",7
    # +CREG: 7,10,"54DB","0F6B0578",7,1,3,0,"abc"
    _re_cell_id_mode_6_7 = \
        re.compile(r'^\s*\+C(E)?REG:\s(?P<n>([0-9]+)),(?P<stat>([0-9]{1,2})),(\")?(?P<lac>([0-9A-Fa-f]*))?(\")?,'
                   r'(\")?(?P<ci>([0-9A-Fa-f]*))?(\")?,(?P<AcT>([0-9]{1,2}))?(,)?(?P<cause_type>([0-9]*))(,)?'
                   r'(?P<reject_cause>([0-9]*))(,)?(?P<csg_stat>([0-9]*))?(,)?(\")?(?P<csginfo>([0-9A-Za-z]*))?(\")?.*$'
                   )

    # <n>=4,5, where +CEREG: <n>,<stat>,[<tac>],[<ci>],[<AcT>][,[<cause_type>],[<reject_cause>],...
    #              ...[<Active-Time>],[<Periodic-RAU>]]
    # +CEREG: 4,5,,,,,,,
    # +CEREG: 4,5,"54DB","0F6B0578",7,,,"00100100","01000111"
    # +CEREG: 5,10,"54DB","0F6B0578",7,1,3,"00100100","01000111"
    # +CEREG: 5,10,"54DB","0F6B0578",7,1,3
    _re_cell_id_mode_4_5 = \
        re.compile(r'^\s*\+CEREG:\s(?P<n>([0-9]+)),(?P<stat>([0-9]{1,2})),(\")?(?P<tac>([0-9A-Fa-f]*))?(\")?,'
                   r'(\")?(?P<ci>([0-9A-Fa-f]*))?(\")?,(?P<AcT>([0-9]{1,2}))?(,)?(?P<cause_type>([0-9]*))?(,)?'
                   r'(?P<reject_cause>([0-9]*))?(,)?(\")?(?P<Active_Time>([0-9A-Fa-f]*))?(\")?(,)?(\")?'
                   r'(?P<Periodic_RAU>([0-9A-Fa-f]*))?(\")?.*$')

    # <n>=3, where +CEREG: <n>,<stat>,[<tac>],[<ci>],[<AcT>][,<cause_type>,<reject_cause>]
    # +CEREG: 3,5,,,,1,2
    # +CEREG: 3,5,"54DB","0F6B0578",7,1,2
    _re_cell_id_mode_3 = \
        re.compile(r'^\s*\+CEREG:\s(?P<n>([0-9]+)),(?P<stat>([0-9]{1,2})),(\")?(?P<tac>([0-9A-Fa-f]*))?(\")?,'
                   r'(\")?(?P<ci>([0-9A-Fa-f]*))?(\")?,(?P<AcT>([0-9]{1,2}))?(,)?(?P<cause_type>([0-9]+))(,)?'
                   r'(?P<reject_cause>([0-9]+)).*$')

    # <n>=2, where +CEREG: <n>,<stat>,[<tac>],[<ci>],[<AcT>]
    # +CEREG: 2,5,,,
    # +CEREG: 2,5,"54DB","0F6B0578",7
    _re_cell_id_mode_2 = \
        re.compile(r'^\s*\+CEREG:\s(?P<n>([0-9]+)),(?P<stat>([0-9]{1,2})),(\")?(?P<tac>([0-9A-Fa-f]*))?(\")?,'
                   r'(\")?(?P<ci>([0-9A-Fa-f]*))?(\")?,(?P<AcT>([0-9]{1,2}))?.*$')

    # <n>=0,1, where +CEREG: <n>,<stat>
    # +CEREG: 1,11
    _re_cell_id_mode_0_1 = \
        re.compile(r'^\s*\+CEREG:\s(?P<n>([0-9]+)),(?P<stat>([0-9]{1,2})).*$')

    def _parse_ip(self, line):
        """
        Parse network registration status and location information:

        +CEREG: 1,11
        or
        +CEREG: 2,5,"54DB","0F6B0578",7
        or
        +CEREG: 3,5,"54DB","0F6B0578",7,1,2
        or
        +CEREG: 5,10,"54DB","0F6B0578",7,1,3,"00100100","01000111"
        or
        +CREG: 7,10,"54DB","0F6B0578",7,1,3,0,"abc"
        """
        def _get_values():
            for key, value in self._regex_helper.groupdict().items():
                self.current_ret[key] = value

        if self._regex_helper.match_compiled(self._re_cell_id_mode_0_1, line):
            _get_values()
            if self.current_ret['n'] in (6, 7) and self._regex_helper.match_compiled(self._re_cell_id_mode_6_7, line):
                _get_values()
            elif self.current_ret['n'] in (4, 5) and self._regex_helper.match_compiled(self._re_cell_id_mode_4_5, line):
                _get_values()
            elif self.current_ret['n'] == 3 and self._regex_helper.match_compiled(self._re_cell_id_mode_3, line):
                _get_values()
            elif self.current_ret['n'] == 2 and self._regex_helper.match_compiled(self._re_cell_id_mode_2, line):
                _get_values()
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

COMMAND_OUTPUT_cell_id_mode_1_execute = """
AT+CEREG?
+CEREG: 1,11
OK
"""

COMMAND_KWARGS_cell_id_mode_1_execute = {}

COMMAND_RESULT_cell_id_mode_1_execute = {
    'n': '1',
    'stat': '11'
}

COMMAND_OUTPUT_cell_id_mode_2_max_execute = """
AT+CEREG?
+CEREG: 2,5,"54DB","0F6B0578",7
OK
"""

COMMAND_KWARGS_cell_id_mode_2_max_execute = {}

COMMAND_RESULT_cell_id_mode_2_max_execute = {
    'n': '2',
    'stat': '5',
    'tac': '54CC',
    'ci': '0F6B9578',
    'AcT': '7'
}

COMMAND_OUTPUT_cell_id_mode_2_min_execute = """
AT+CEREG?
+CEREG: 2,5,,,
OK
"""

COMMAND_KWARGS_cell_id_mode_2_min_execute = {}

COMMAND_RESULT_cell_id_mode_2_min_execute = {
    'n': '2',
    'stat': '5',
    'tac': '',
    'ci': '',
    'AcT': None
}

COMMAND_OUTPUT_cell_id_mode_3_max_execute = """
AT+CEREG?
+CEREG: 3,5,"54DB","0F6B0578",15,1,2
OK
"""

COMMAND_KWARGS_cell_id_mode_3_max_execute = {}

COMMAND_RESULT_cell_id_mode_3_max_execute = {
    'n': '2',
    'stat': '5',
    'tac': '54CC',
    'ci': '0F6B9578',
    'AcT': '15',
    'cause_type': '1',
    'reject_cause': '2'
}

COMMAND_OUTPUT_cell_id_mode_3_min_execute = """
AT+CEREG?
+CEREG: 3,5,,,,1,2
OK
"""

COMMAND_KWARGS_cell_id_mode_3_min_execute = {}

COMMAND_RESULT_cell_id_mode_3_min_execute = {
    'n': '3',
    'stat': '5',
    'tac': '',
    'ci': '',
    'AcT': None,
    'cause_type': '1',
    'reject_cause': '2'
}

COMMAND_OUTPUT_cell_id_mode_4_5_v1_execute = """
AT+CEREG?
+CEREG: 4,5,,,,,,,
OK
"""

COMMAND_KWARGS_cell_id_mode_4_5_v1_execute = {}

COMMAND_RESULT_cell_id_mode_4_5_v1_execute = {
    'n': '4',
    'stat': '5',
    'tac': '',
    'ci': '',
    'AcT': None,
    'cause_type': '',
    'reject_cause': '',
    'Active_Time': '',
    'Periodic_RAU': ''
}

COMMAND_OUTPUT_cell_id_mode_4_5_v2_execute = """
AT+CEREG?
+CEREG: 4,5,"54DB","0F6B0578",7,,"00100100","01000111"
OK
"""

COMMAND_KWARGS_cell_id_mode_4_5_v2_execute = {}

COMMAND_RESULT_cell_id_mode_4_5_v2_execute = {
    'n': '4',
    'stat': '5',
    'tac': '54DB',
    'ci': '0F6B0578',
    'AcT': '7',
    'cause_type': '',
    'reject_cause': '',
    'Active_Time': '00100100',
    'Periodic_RAU': '01000111'
}

COMMAND_OUTPUT_cell_id_mode_4_5_v3_execute = """
AT+CEREG?
+CEREG: 5,10,"54DB","0F6B0578",7,1,3,"00100100","01000111"
OK
"""

COMMAND_KWARGS_cell_id_mode_4_5_v3_execute = {}

COMMAND_RESULT_cell_id_mode_4_5_v3_execute = {
    'n': '5',
    'stat': '10',
    'tac': '54DB',
    'ci': '0F6B0578',
    'AcT': '7',
    'cause_type': '1',
    'reject_cause': '3',
    'Active_Time': '00100100',
    'Periodic_RAU': '01000111'
}

COMMAND_OUTPUT_cell_id_mode_4_5_v4_execute = """
AT+CEREG?
+CEREG: 5,10,"54DB","0F6B0578",7,1,3
OK
"""

COMMAND_KWARGS_cell_id_mode_4_5_v4_execute = {}

COMMAND_RESULT_cell_id_mode_4_5_v4_execute = {
    'n': '5',
    'stat': '10',
    'tac': '54DB',
    'ci': '0F6B0578',
    'AcT': '7',
    'cause_type': '1',
    'reject_cause': '3',
    'Active_Time': '',
    'Periodic_RAU': ''
}

COMMAND_OUTPUT_cell_id_mode_6_7_v1_execute = """
AT+CEREG?
+CREG: 6,5,,,,1,2,0
OK
"""

COMMAND_KWARGS_cell_id_mode_6_7_v1_execute = {}

COMMAND_RESULT_cell_id_mode_6_7_v1_execute = {
    'n': '6',
    'stat': '5',
    'lac': '',
    'ci': '',
    'AcT': None,
    'cause_type': '1',
    'reject_cause': '2',
    'csg_stat': '0',
    'csginfo': ''
}

COMMAND_OUTPUT_cell_id_mode_6_7_v2_execute = """
AT+CEREG?
+CREG: 7,10,"54DB","0F6B0578",7
OK
"""

COMMAND_KWARGS_cell_id_mode_6_7_v2_execute = {}

COMMAND_RESULT_cell_id_mode_6_7_v2_execute = {
    'n': '7',
    'stat': '10',
    'lac': '54DB',
    'ci': '0F6B0578',
    'AcT': '7',
    'cause_type': '',
    'reject_cause': '',
    'csg_stat': '',
    'csginfo': ''
}

COMMAND_OUTPUT_cell_id_mode_6_7_v3_execute = """
AT+CEREG?
+CREG: 7,10,"54DB","0F6B0578",7,1,3,0,"abc"
OK
"""

COMMAND_KWARGS_cell_id_mode_6_7_v3_execute = {}

COMMAND_RESULT_cell_id_mode_6_7_v3_execute = {
    'n': '7',
    'stat': '10',
    'lac': '54DB',
    'ci': '0F6B0578',
    'AcT': '7',
    'cause_type': '1',
    'reject_cause': '3',
    'csg_stat': '0',
    'csginfo': 'abc'
}
