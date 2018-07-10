# -*- coding: utf-8 -*-
"""
AT+CIMI .

AT commands specification:
https://portal.3gpp.org/desktopmodules/Specifications/SpecificationDetails.aspx?specificationId=1515
(always check against latest version of standard)
"""

__author__ = 'Lukasz Blaszkiewicz, Kamil Kania, Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'kamil.kania@nokia.com, grzegorz.latuszek@nokia.com'

import re

from moler.cmd.at.at import AtCmd, AtCommandModeNotSupported


class AtCmdGetIMSI(AtCmd):
    def __init__(self, connection=None, operation='execute'):
        """Create instance of AtCmdGetIMSI class"""
        super(AtCmdGetIMSI, self).__init__(connection, operation)
        if operation == 'read':
            raise AtCommandModeNotSupported("{} operation no supported for: {}".format(operation, self))
        self.set_at_command_string(command_base_string="AT+CIMI")

    def parse_command_output(self):
        """
        AT+CIMI
        49009123123123
        OK
        """
        if self.operation == "test":  # empty response in test mode since +CIMI doesn't have subparameters
            self.set_result({})
        else:
            match = re.search(r"(?P<imsi>\d+)\nOK", self.command_output)
            if match:
                self.set_result(match.groupdict())


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
at+cimi
440801200189934
OK
"""

COMMAND_KWARGS_ver_execute = {'operation': 'execute'}

COMMAND_RESULT_ver_execute = {
    'imsi': '440801200189934'
}

# -----------------------------------------------------------------------------

COMMAND_OUTPUT_ver_test = """
at+cimi=?
OK
"""

COMMAND_KWARGS_ver_test = {'operation': 'test'}

COMMAND_RESULT_ver_test = {}
