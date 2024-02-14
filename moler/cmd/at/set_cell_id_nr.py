# -*- coding: utf-8 -*-
"""
AT+C5GREG={}

AT commands specification:
google for: 3gpp specification 27.007
(always check against latest version of standard)
"""

__author__ = 'Jakub Kochaniak'
__copyright__ = 'Copyright (C) 2023, Nokia'
__email__ = 'jakub.kochaniak@nokia.com'

from moler.cmd.at.genericat import GenericAtCommand


class SetCellIdNr(GenericAtCommand):

    def __init__(self, selected_mode, connection=None, prompt=None, newline_chars=None, runner=None):
        """
        Create instance of SetCellIdNr class and command to set registered NR cell presentation of an unsolicited code.

        :param selected_mode: Set 5G registration mode for AT command: AT+C5GREG="selected_mode", but verify with
                              latest 3gpp specification 27.007: 0-'disable network', 1-'enable network',
                              2-'enable network, location information unsolicited result code',
                              3-'enable network, location and 5GMM cause value information unsolicited result code',
                              4-'enable network, location, cause value, CAG status unsolicited result code',
                              5-'enable network, location, cause value, CAG status and CAG cell status unsolicited '
                              'result code'
        :param connection: Moler connection to device, terminal when command is executed.
        :param prompt: prompt where we start from.
        :param newline_chars: Characters to split local lines - list.
        :param runner: Runner to run command.
        """
        super(SetCellIdNr, self).__init__(connection, operation='execute', prompt=prompt,
                                          newline_chars=newline_chars, runner=runner)
        self.selected_mode = int(selected_mode)
        self.ret_required = False

    def build_command_string(self):
        return f"AT+C5GREG={self.selected_mode}"


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

COMMAND_OUTPUT_nr_off = """
AT+C5GREG=0

OK
"""

COMMAND_KWARGS_nr_off = {"selected_mode": 0}

COMMAND_RESULT_nr_off = {}

COMMAND_OUTPUT_nr_on_with_data = """
AT+C5GREG=2

OK
"""

COMMAND_KWARGS_nr_on_with_data = {"selected_mode": 2}

COMMAND_RESULT_nr_on_with_data = {}
