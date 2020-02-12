# -*- coding: utf-8 -*-
"""
AT+CGATT? . Check attach state: attached/detached

AT commands specification:
google for: 3gpp specification 27.007
(always check against latest version of standard)
"""

__author__ = ' Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import re

from moler.cmd.at.genericat import GenericAtCommand
from moler.exceptions import ParsingDone


class GetAttachState(GenericAtCommand):
    """
    Command to check attach state. Example output:

    AT+CGATT?
    +CGATT: 1
    OK
    """
    def __init__(self, connection=None, prompt=None, newline_chars=None, runner=None):
        """Create instance of GetAttachState class"""
        super(GetAttachState, self).__init__(connection, operation="read", prompt=prompt,
                                             newline_chars=newline_chars, runner=runner)

    def build_command_string(self):
        return "AT+CGATT?"

    def on_new_line(self, line, is_full_line):
        """
        Method to parse command output. Will be called after line with command echo.

        +CGATT: 1
        OK

        Write your own implementation but don't forget to call on_new_line from base class

        :param line: Line to parse, new lines are trimmed
        :param is_full_line:  False for chunk of line; True on full line (NOTE: new line character removed)
        :return: None
        """
        if is_full_line:
            try:
                self._parse_attach_state(line)
            except ParsingDone:
                pass
        return super(GetAttachState, self).on_new_line(line, is_full_line)

    _re_attach_state = re.compile(r'^\s*\+CGATT:\s*(?P<state_code>[01])\s*$')
    _states = {0: "detached", 1: "attached"}

    def _parse_attach_state(self, line):
        """
        Parse IMSI number that should look like:

        +CGATT: 1
        """
        if self._regex_helper.match_compiled(self._re_attach_state, line):
            state_code = int(self._regex_helper.group("state_code"))
            self.current_ret['state'] = self._states[state_code]
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

COMMAND_OUTPUT_ver_attached = """
AT+CGATT?
+CGATT: 1
OK
"""

COMMAND_KWARGS_ver_attached = {}

COMMAND_RESULT_ver_attached = {'state': 'attached'}

# -----------------------------------------------------------------------------

COMMAND_OUTPUT_ver_detached = """
AT+CGATT?
+CGATT: 0
OK
"""

COMMAND_KWARGS_ver_detached = {}

COMMAND_RESULT_ver_detached = {'state': 'detached'}
