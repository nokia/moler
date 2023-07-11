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
    """
    Command to get cell registration status. Example output:

    +C5GREG: <n>,<stat>[,[<lac>],[<ci>],[<AcT>],[<rac>][,<cause_type>,<reject_cause>]]

    OK
    or
    +C5GREG: <n>,<stat>[,[<lac>],[<ci>],[<AcT>],[<rac>][,[<cause_type>],[<reject_cause>]...
    ...[,[<Active-Time>],[<Periodic-RAU>],[<GPRS-READY-timer>]]]]

    OK
    """
    def __init__(self, connection=None, prompt=None, newline_chars=None, runner=None):
        """Create instance of GetCellIdGsm class"""
        super(GetCellIdNr, self).__init__(connection, operation='execute', prompt=prompt,
                                          newline_chars=newline_chars, runner=runner)
        self.current_ret = {}

    def build_command_string(self):
        return "AT+C5GREG?"

    def on_new_line(self, line, is_full_line):
        """
        Method to parse command output. Will be called after line with command echo.

        +C5GREG: <n>,<stat>[,[<lac>],[<ci>],[<AcT>],[<rac>][,<cause_type>,<reject_cause>]]

        OK
        or
        +C5GREG: <n>,<stat>[,[<lac>],[<ci>],[<AcT>],[<rac>][,[<cause_type>],[<reject_cause>]...
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
        return super(GetCellIdNr, self).on_new_line(line, is_full_line)

    # <n>=4,5, where +C5GREG: <n>,<stat>[,[<tac>],[<ci>],[<AcT>],[<Allowed_NSSAI_length>],[<Allowed_NSSAI>]...
    #                ...[,<cause_type>,<reject_cause>]][,<cag_stat>][,<caginfo>]
    # +C5GREG: 4,5,,,,,,1,2
    # +C5GREG: 5,5,"54DB","0F6B0578",7,2,"aB",1,2,123,"info"
    _re_cell_id_mode_4_5 = \
        re.compile(r'^\s*\+C5GREG:\s(?P<n>([0-9]+)),(?P<stat>([0-9]{1,2}))(,)?(\")?(?P<tac>([0-9A-Fa-f]*))?(\")?(,)?'
                   r'(\")?(?P<ci>([0-9A-Fa-f]*))?(\")?(,)?(?P<AcT>([0-9]{1,2}))?(,)?'
                   r'(?P<Allowed_NSSAI_length>([0-9]+))?(,)?(\")?(?P<Allowed_NSSAI>([0-9A-Za-z]*))?(\")?(,)?'
                   r'(?P<cause_type>([0-9]*))?(,)?(?P<reject_cause>([0-9]*))?(,)?(?P<cag_stat>([0-9]*))?(,)?(\")?'
                   r'(?P<caginfo>([0-9A-Za-z]*))?(\")?.*$')

    # <n>=3, where +C5GREG: <n>,<stat>[,[<tac>],[<ci>],[<AcT>],[<Allowed_NSSAI_length>],[<Allowed_NSSAI>]...
    #              ...[,<cause_type>,<reject_cause>]]
    # +C5GREG: 3,5,,,,,,1,2
    # +C5GREG: 3,5,"54DB","0F6B0578",7,2,"aB",1,2
    _re_cell_id_mode_3 = \
        re.compile(r'^\s*\+C5GREG:\s(?P<n>([0-9]+)),(?P<stat>([0-9]{1,2}))(,)?(\")?(?P<tac>([0-9A-Fa-f]*))?(\")?(,)?'
                   r'(\")?(?P<ci>([0-9A-Fa-f]*))?(\")?(,)?(?P<AcT>([0-9]{1,2}))?(,)?'
                   r'(?P<Allowed_NSSAI_length>([0-9]+))?(,)?(\")?(?P<Allowed_NSSAI>([0-9A-Za-z]*))?(\")?(,)?'
                   r'(?P<cause_type>([0-9]*))?(,)?(?P<reject_cause>([0-9]*))?.*$')

    # <n>=2, where +C5GREG: <n>,<stat>[,[<tac>],[<ci>],[<AcT>],[<Allowed_NSSAI_length>],[<Allowed_NSSAI>]]
    # +C5GREG: 2,5,,,,,
    # +C5GREG: 2,5,"54DB","0F6B0578",7,2,"aB"
    _re_cell_id_mode_2 = \
        re.compile(r'^\s*\+C5GREG:\s(?P<n>([0-9]+)),(?P<stat>([0-9]{1,2}))(,)?(\")?(?P<tac>([0-9A-Fa-f]*))?(\")?(,)?'
                   r'(\")?(?P<ci>([0-9A-Fa-f]*))?(\")?(,)?(?P<AcT>([0-9]{1,2}))?(,)?'
                   r'(?P<Allowed_NSSAI_length>([0-9]+))?(,)?(\")?(?P<Allowed_NSSAI>([0-9A-Za-z]*))?(\")?.*$')

    # <n>=0,1, where +C5GREG: <n>,<stat>
    # +C5GREG: 1,11
    _re_cell_id_mode_0_1 = \
        re.compile(r'^\s*\+C5GREG:\s(?P<n>([0-9]+)),(?P<stat>([0-9]{1,2})).*$')

    def _parse_ip(self, line):
        """
        Parse network registration status and location information:

        +C5GREG: 1,11
        or
        +C5GREG: 2,5,"54DB","0F6B0578",7,2,"aB"
        or
        +C5GREG: 3,5,"54DB","0F6B0578",7,2,"aB",1,2
        or
        +C5GREG: 5,5,"54DB","0F6B0578",7,2,"aB",1,2,123,"info"
        """
        def _get_values():
            for key, value in self._regex_helper.groupdict().items():
                self.current_ret[key] = value

        if self._regex_helper.match_compiled(self._re_cell_id_mode_0_1, line):
            _get_values()
            if self.current_ret['n'] in (4, 5) and self._regex_helper.match_compiled(self._re_cell_id_mode_4_5, line):
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
AT+C5GREG?
+C5GREG: 1,11
OK
"""

COMMAND_KWARGS_cell_id_mode_1_execute = {}

COMMAND_RESULT_cell_id_mode_1_execute = {
    'n': '1',
    'stat': '11'
}

COMMAND_OUTPUT_cell_id_mode_2_max_execute = """
AT+C5GREG?
+C5GREG: 2,5,"54DB","0F6B0578",7,2,"aB"
OK
"""

COMMAND_KWARGS_cell_id_mode_2_max_execute = {}

COMMAND_RESULT_cell_id_mode_2_max_execute = {
    'n': '2',
    'stat': '5',
    'tac': '54DB',
    'ci': '0F6B0578',
    'AcT': '7',
    'Allowed_NSSAI_length': '2',
    'Allowed_NSSAI': 'aB'
}

COMMAND_OUTPUT_cell_id_mode_2_min_execute = """
AT+C5GREG?
+C5GREG: 2,5,,,,,
OK
"""

COMMAND_KWARGS_cell_id_mode_2_min_execute = {}

COMMAND_RESULT_cell_id_mode_2_min_execute = {
    'n': '2',
    'stat': '5',
    'tac': '',
    'ci': '',
    'AcT': None,
    'Allowed_NSSAI_length': None,
    'Allowed_NSSAI': ''
}

COMMAND_OUTPUT_cell_id_mode_3_max_execute = """
AT+C5GREG?
+C5GREG: 3,5,"54DB","0F6B0578",7,2,"aB",1,2
OK
"""

COMMAND_KWARGS_cell_id_mode_3_max_execute = {}

COMMAND_RESULT_cell_id_mode_3_max_execute = {
    'n': '3',
    'stat': '5',
    'tac': '54DB',
    'ci': '0F6B0578',
    'AcT': '7',
    'Allowed_NSSAI_length': '2',
    'Allowed_NSSAI': 'aB',
    'cause_type': '1',
    'reject_cause': '2'
}

COMMAND_OUTPUT_cell_id_mode_3_min_execute = """
AT+C5GREG?
+C5GREG: 3,5,,,,,,1,2
OK
"""

COMMAND_KWARGS_cell_id_mode_3_min_execute = {}

COMMAND_RESULT_cell_id_mode_3_min_execute = {
    'n': '3',
    'stat': '5',
    'tac': '',
    'ci': '',
    'AcT': None,
    'Allowed_NSSAI_length': None,
    'Allowed_NSSAI': '',
    'cause_type': '1',
    'reject_cause': '2'
}

COMMAND_OUTPUT_cell_id_mode_4_5_v1_execute = """
AT+C5GREG?
+C5GREG: 4,5,,,,,,1,2
OK
"""

COMMAND_KWARGS_cell_id_mode_4_5_v1_execute = {}

COMMAND_RESULT_cell_id_mode_4_5_v1_execute = {
    'n': '4',
    'stat': '5',
    'tac': '',
    'ci': '',
    'AcT': None,
    'Allowed_NSSAI_length': None,
    'Allowed_NSSAI': '',
    'cause_type': '1',
    'reject_cause': '2',
    'cag_stat': '',
    'caginfo': ''
}

COMMAND_OUTPUT_cell_id_mode_4_5_v2_execute = """
AT+C5GREG?
+C5GREG: 5,5,"54DB","0F6B0578",7,2,"aB",1,2,123,"info"
OK
"""

COMMAND_KWARGS_cell_id_mode_4_5_v2_execute = {}

COMMAND_RESULT_cell_id_mode_4_5_v2_execute = {
    'n': '4',
    'stat': '5',
    'tac': '54DB',
    'ci': '0F6B0578',
    'AcT': '7',
    'Allowed_NSSAI_length': '2',
    'Allowed_NSSAI': 'aB',
    'cause_type': '1',
    'reject_cause': '2',
    'cag_stat': '123',
    'caginfo': 'info'
}
