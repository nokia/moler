# -*- coding: utf-8 -*-
"""
AT+COPS

AT commands specification:
google for: 3gpp specification 27.007
(always check against latest version of standard)
"""

__author__ = 'Adam Klekowski'
__copyright__ = 'Copyright (C) 2021, Nokia'
__email__ = 'adam.klekowski@nokia.com'

import re

from moler.cmd.at.genericat import GenericAtCommand
from moler.exceptions import ParsingDone, WrongUsage


class SetMode(GenericAtCommand):
    """
    Command to set mode (automatic, lte, gsm, wcdma).
    """
    mode2cops_value = {"automatic": '0',
                       "lte": '0,0,0,7',
                       "gsm": '0,0,0,3',
                       "wcdma": '0,0,0,6'}

    def __init__(self, selected_mode, connection=None, prompt=None, newline_chars=None, runner=None):
        """Create instance of SetMode class"""
        super(SetMode, self).__init__(connection, operation='execute', prompt=prompt,
                                      newline_chars=newline_chars, runner=runner)
        self.selected_mode = selected_mode.lower()

        if self.selected_mode not in SetMode.mode2cops_value:
            raise WrongUsage('\"{}\" is not correct mode. Available modes: {}.'.format(
                self.selected_mode, list(SetMode.mode2cops_value.keys())))

        self.ret_required = False

    def build_command_string(self):
        return "AT+COPS={}".format(SetMode.mode2cops_value[self.selected_mode])


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

COMMAND_OUTPUT_automatic_lower = """
AT+COPS=0

OK
"""

COMMAND_KWARGS_automatic_lower = {"selected_mode": "automatic"}

COMMAND_RESULT_automatic_lower = {}

COMMAND_OUTPUT_lte_upper = """
AT+COPS=0,0,0,7

OK
"""

COMMAND_KWARGS_lte_upper = {"selected_mode": "LTE"}

COMMAND_RESULT_lte_upper = {}
