# -*- coding: utf-8 -*-
"""
AT+CGATT=0 . Detach

AT commands specification:
google for: 3gpp specification 27.007
(always check against latest version of standard)
"""

__author__ = ' Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

from moler.cmd.at.genericat import GenericAtCommand


class Detach(GenericAtCommand):
    """
    Command to trigger detach. Example output:

    AT+CGATT=0
    OK
    """
    def __init__(self, connection=None, prompt=None, newline_chars=None, runner=None):
        """Create instance of Detach class"""
        super(Detach, self).__init__(connection, operation="execute", prompt=prompt,
                                     newline_chars=newline_chars, runner=runner)
        self.ret_required = False

    def build_command_string(self):
        return "AT+CGATT=0"


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

COMMAND_OUTPUT_ver_execute = """
AT+CGATT=0
OK
"""

COMMAND_KWARGS_ver_execute = {}

COMMAND_RESULT_ver_execute = {}
