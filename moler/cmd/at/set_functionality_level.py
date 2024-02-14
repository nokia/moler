# -*- coding: utf-8 -*-
"""
AT+CFUN

AT commands specification:
google for: 3gpp specification 27.007
(always check against latest version of standard)
"""

__author__ = 'Kamil Pielka'
__copyright__ = 'Copyright (C) 2022, Nokia'
__email__ = 'kamil.pielka@nokia.com'

from moler.cmd.at.genericat import GenericAtCommand


class SetFunctionalityLevel(GenericAtCommand):
    """
    Command to set the level of functionality for UE. Example output:

    AT+CFUN=1
    OK
    """
    def __init__(self, fun_level, rst=None, connection=None, prompt=None, newline_chars=None, runner=None):
        """Create instance of SetFunctionalityLevel class
        :param fun_level: UE's level of functionality
                          Possible valueATs are:
                          0 - minimum functionality
                          1 - full functionality
                          2 - disable phone transmit RF circuits only
                          3 - disable phone receive RF circuits only
                          4 - disable phone both transmit and receive RF circuits
                          5...127 - reserved for manufacturers as intermediate states between full and minimum
                                    functionality
        :param rst: whether to restart UE before setting level of functionality
                    None - there is not provide openly any value in command (AT command uses default value)
                    0 - not reset UE before setting level of functionality (default value)
                    1 - reset UE before setting level of functionality (level of functionality must be 1)
        :param connection: moler connection to device
        :param prompt: start prompt (on system where command cd starts)
        :param newline_chars: Characters to split lines
        :param runner: Runner to run command
        """
        super(SetFunctionalityLevel, self).__init__(connection=connection, operation='execute', prompt=prompt,
                                                    newline_chars=newline_chars, runner=runner)
        self.fun_level = fun_level
        self.rst = rst
        self.ret_required = False

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.
        :return: String representation of command to send over connection to device.
        """
        if self.rst is None:
            return f"AT+CFUN={self.fun_level}"
        else:
            return f"AT+CFUN={self.fun_level},{self.rst}"


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

COMMAND_OUTPUT_default_parameters = """
AT+CFUN=1
OK
"""

COMMAND_KWARGS_default_parameters = {"fun_level": "1"}

COMMAND_RESULT_default_parameters = {}

COMMAND_OUTPUT_all_parameters = """
AT+CFUN=1,1
OK
"""

COMMAND_KWARGS_all_parameters = {"fun_level": "1", "rst": "1"}

COMMAND_RESULT_all_parameters = {}
