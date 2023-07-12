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
    Command to get NR cell registration status. Example output:

    +C5GREG: <n>,<stat>[,[<lac>],[<ci>],[<AcT>],[<rac>][,[<cause_type>],[<reject_cause>]...
    ...[,[<Active-Time>],[<Periodic-RAU>],[<GPRS-READY-timer>]]]]

    OK
    """
    def __init__(self, connection=None, prompt=None, newline_chars=None, runner=None):
        """Create instance of GetCellIdNr class"""
        super(GetCellIdNr, self).__init__(connection, operation='execute', prompt=prompt,
                                          newline_chars=newline_chars, runner=runner)
        self.current_ret = dict()

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
                self._parse_cell_data_nr(line)
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
                   r'(?P<Allowed_NSSAI_length>([0-9]+))?(,)?(\")?(?P<Allowed_NSSAI>([0-9A-Za-z.]*))?(\")?(,)?'
                   r'(?P<cause_type>([0-9]*))?(,)?(?P<reject_cause>([0-9]*))?(,)?(?P<cag_stat>([0-9]*))?(,)?(\")?'
                   r'(?P<caginfo>([0-9A-Za-z]*))?(\")?.*$')

    # <n>=3, where +C5GREG: <n>,<stat>[,[<tac>],[<ci>],[<AcT>],[<Allowed_NSSAI_length>],[<Allowed_NSSAI>]...
    #              ...[,<cause_type>,<reject_cause>]]
    # +C5GREG: 3,5,,,,,,1,2
    # +C5GREG: 3,5,"54DB","0F6B0578",7,2,"aB",1,2
    _re_cell_id_mode_3 = \
        re.compile(r'^\s*\+C5GREG:\s(?P<n>([0-9]+)),(?P<stat>([0-9]{1,2}))(,)?(\")?(?P<tac>([0-9A-Fa-f]*))?(\")?(,)?'
                   r'(\")?(?P<ci>([0-9A-Fa-f]*))?(\")?(,)?(?P<AcT>([0-9]{1,2}))?(,)?'
                   r'(?P<Allowed_NSSAI_length>([0-9]+))?(,)?(\")?(?P<Allowed_NSSAI>([0-9A-Za-z.]*))?(\")?(,)?'
                   r'(?P<cause_type>([0-9]*))?(,)?(?P<reject_cause>([0-9]*))?.*$')

    # <n>=2, where +C5GREG: <n>,<stat>[,[<tac>],[<ci>],[<AcT>],[<Allowed_NSSAI_length>],[<Allowed_NSSAI>]]
    # +C5GREG: 2,5,,,,,
    # +C5GREG: 2,5,"54DB","0F6B0578",7,2,"aB"
    _re_cell_id_mode_2 = \
        re.compile(r'^\s*\+C5GREG:\s(?P<n>([0-9]+)),(?P<stat>([0-9]{1,2}))(,)?(\")?(?P<tac>([0-9A-Fa-f]*))?(\")?(,)?'
                   r'(\")?(?P<ci>([0-9A-Fa-f]*))?(\")?(,)?(?P<AcT>([0-9]{1,2}))?(,)?'
                   r'(?P<Allowed_NSSAI_length>([0-9]+))?(,)?(\")?(?P<Allowed_NSSAI>([0-9A-Za-z.]*))?(\")?.*$')

    # <n>=1, where +C5GREG: <n>[,[<tac>],[<ci>],[<AcT>],[<Allowed_NSSAI_length>],[<Allowed_NSSAI>]]
    # +C5GREG: 1,"0F6B0578",7,2,"aB" - option regarding to manual tests
    _re_cell_id_mode_1 = \
        re.compile(r'^\s*\+C5GREG:\s(?P<n>([0-9]+)),\"(?P<tac>([0-9A-Fa-f]*))?(\")?(,)?(\")?'
                   r'(?P<ci>([0-9A-Fa-f]*))?(\")?(,)?(?P<AcT>([0-9]{1,2}))?(,)?(?P<Allowed_NSSAI_length>([0-9]+))?(,)?'
                   r'(\")?(?P<Allowed_NSSAI>([0-9A-Za-z.]*))?(\")?.*$')

    # <n>=0,1, where +C5GREG: <n>,<stat>
    # +C5GREG: 1,11
    _re_cell_id_mode_0_1 = re.compile(r'^\s*\+C5GREG:\s(?P<n>([0-9]+)),(?P<stat>([0-9]{1,2})).*$')

    # <n>=0, where +C5GREG: <n>
    # +C5GREG: 0
    _re_cell_id_mode_0 = re.compile(r'^\s*\+C5GREG:\s(?P<n>([0-9]+))(,)?.*$')

    # +C5GREG: <output_data>
    _re_cell_id_data = re.compile(r'^\s*\+C5GREG:\s(?P<output_data>\w+\S+).*$')

    def _parse_cell_data_nr(self, line):
        """
        Parse network registration status and location information:

        +C5GREG: 1,11
        or
        +C5GREG: 1,"54DB","0F6B0578",7,2,"aB"
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

        if self._regex_helper.match_compiled(self._re_cell_id_mode_0, line):
            _get_values()
            _variant = int(self.current_ret['n'])
            if _variant in (4, 5) and self._regex_helper.match_compiled(self._re_cell_id_mode_4_5, line):
                _get_values()
            elif _variant == 3 and self._regex_helper.match_compiled(self._re_cell_id_mode_3, line):
                _get_values()
            elif _variant == 2 and self._regex_helper.match_compiled(self._re_cell_id_mode_2, line):
                _get_values()
            elif _variant == 1 and self._regex_helper.match_compiled(self._re_cell_id_mode_1, line):
                _get_values()
            elif _variant == 1 and self._regex_helper.match_compiled(self._re_cell_id_mode_0_1, line):
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

COMMAND_OUTPUT_cell_id_nr_v1_1 = """
AT+C5GREG?
+C5GREG: 1,11

OK
"""

COMMAND_KWARGS_cell_id_nr_v1_1 = {}

COMMAND_RESULT_cell_id_nr_v1_1 = {
    'n': '1',
    'stat': '11',
    'output_data': '1,11'
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
    'output_data': '1,"1964","260768000",11,4,"01.D143A5"'
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
    'output_data': '2,5,"54DB","0F6B0578",7,2,"aB"'
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
    'tac': '',
    'ci': '',
    'AcT': None,
    'Allowed_NSSAI_length': None,
    'Allowed_NSSAI': '',
    'output_data': '2,5,,,,,'
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
    'output_data': '3,5,"54DB","0F6B0578",7,2,"aB",1,2'
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
    'tac': '',
    'ci': '',
    'AcT': None,
    'Allowed_NSSAI_length': None,
    'Allowed_NSSAI': '',
    'cause_type': '1',
    'reject_cause': '2',
    'output_data': '3,5,,,,,,1,2'
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
    'tac': '',
    'ci': '',
    'AcT': None,
    'Allowed_NSSAI_length': None,
    'Allowed_NSSAI': '',
    'cause_type': '1',
    'reject_cause': '2',
    'cag_stat': '',
    'caginfo': '',
    'output_data': '4,5,,,,,,1,2'
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
    'output_data': '5,5,"54DB","0F6B0578",7,2,"aB",1,2,123,"info"'
}
