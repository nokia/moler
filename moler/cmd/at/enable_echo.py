# -*- coding: utf-8 -*-
"""
ATE1

AT commands specification:
google for: 3gpp specification 27.007
(always check against latest version of standard)
"""

__author__ = 'Adam Klekowski'
__copyright__ = 'Copyright (C) 2020-2021, Nokia'
__email__ = 'adam.klekowski@nokia.com'

from moler.cmd.at.genericat import GenericAtCommand


class EnableEcho(GenericAtCommand):
    """
    Command to enable echo. Example output:

    ATE1
    OK
    """
    def __init__(self, connection=None, prompt=None, newline_chars=None, runner=None):
        """
        :param connection: moler connection to device
        :param prompt: start prompt (on system where command cd starts)
        :param newline_chars: Characters to split lines
        :param runner: Runner to run command
        """
        super(EnableEcho, self).__init__(connection, operation="execute", prompt=prompt,
                                         newline_chars=newline_chars, runner=runner)
        self.ret_required = False

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.
        :return: String representation of command to send over connection to device.
        """
        return "ATE1"


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
ATE1
OK
"""

COMMAND_KWARGS_ver_execute = {}

COMMAND_RESULT_ver_execute = {}
