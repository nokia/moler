# -*- coding: utf-8 -*-
"""
AT+CGATT=1 . Attach

AT commands specification:
https://portal.3gpp.org/desktopmodules/Specifications/SpecificationDetails.aspx?specificationId=1515
(always check against latest version of standard)
"""

__author__ = ' Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

from moler.cmd.at.at import AtCmd, AtCommandModeNotSupported


class AtCmdAttach(AtCmd):
    def __init__(self, connection=None, operation='execute'):
        """Create instance of AtCmdAttach class"""
        super(AtCmdAttach, self).__init__(connection, operation)
        if operation != 'execute':
            raise AtCommandModeNotSupported("{} operation no supported for: {}".format(operation, self))
        self.set_at_command_string(command_base_string="AT+CGATT=1")
        self.timeout = 180

    def parse_command_output(self):
        """
        AT+CGATT=1
        OK
        """
        self.set_result({})


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
AT+CGATT=1
OK
"""

COMMAND_KWARGS_ver_execute = {'operation': 'execute'}

COMMAND_RESULT_ver_execute = {}

# -----------------------------------------------------------------------------
