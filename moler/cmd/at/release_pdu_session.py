# -*- coding: utf-8 -*-
"""
AT$QCRMCALL=0,1

AT commands specification:
google for: 3gpp specification 27.007
(always check against the latest version of standard)
"""

__author__ = 'Adam Klekowski'
__copyright__ = 'Copyright (C) 2023, Nokia'
__email__ = 'adam.klekowski@nokia.com'

from moler.cmd.at.genericat import GenericAtCommand


class ReleasePduSession(GenericAtCommand):
    """
    Command to release PDU session. Example output:

    AT$QCRMCALL=0,1
    OK
    """
    def __init__(self, connection=None, prompt=None, newline_chars=None, runner=None):
        """
        Create instance of ReleasePduSession class
        :param connection: moler connection to device
        :param prompt: start prompt (on system where command cd starts)
        :param newline_chars: Characters to split lines
        :param runner: Runner to run command
        """
        super(ReleasePduSession, self).__init__(connection, operation='execute', prompt=prompt,
                                                newline_chars=newline_chars, runner=runner)
        self.ret_required = False

    def build_command_string(self):
        return "AT$QCRMCALL=0,1"


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
AT$QCRMCALL=0,1
OK
"""

COMMAND_KWARGS_ver_execute = {}

COMMAND_RESULT_ver_execute = {}
