# -*- coding: utf-8 -*-
"""
AT .

AT commands specification:
google for: 3gpp specification 27.007
(always check against latest version of standard)
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'


from moler.cmd.at.genericat import GenericAtCommand


class At(GenericAtCommand):
    """
    Command to check if AT console is operable. Example output:

    AT
    OK
    """
    def __init__(self, connection=None, prompt=None, newline_chars=None, runner=None):
        """
        Create instance of At class
        :param connection: connection used to send command and receive its output
        """
        super(At, self).__init__(connection, operation="execute", prompt=prompt,
                                 newline_chars=newline_chars, runner=runner)
        self.ret_required = False

    def build_command_string(self):
        return "AT"


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
AT
OK
"""

COMMAND_KWARGS_ver_execute = {}

COMMAND_RESULT_ver_execute = {}
