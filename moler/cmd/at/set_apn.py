# -*- coding: utf-8 -*-
"""
AT+CGDCONT

AT commands specification:
google for: 3gpp specification 27.007
(always check against latest version of standard)
"""

__author__ = 'Adam Klekowski'
__copyright__ = 'Copyright (C) 2021-2023, Nokia'
__email__ = 'adam.klekowski@nokia.com'

from moler.cmd.at.genericat import GenericAtCommand


class SetApn(GenericAtCommand):
    """
    Command to set apn.
    """
    def __init__(self, apn_name, context_identifier='1', pdp_type='IPV4V6',
                 connection=None, prompt=None, newline_chars=None, runner=None):
        """
        :apn_name: APN name to set on UE
        :context_identifier: context identifier of setting APN
        :pdp_type: PDP type (usually IP or IPV4V6)
        :param connection: moler connection to device
        :param prompt: start prompt (on system where command cd starts)
        :param newline_chars: Characters to split lines
        :param runner: Runner to run command
        """
        super(SetApn, self).__init__(connection, operation='execute', prompt=prompt,
                                     newline_chars=newline_chars, runner=runner)
        self.apn_name = apn_name.strip('\"')
        self.context_identifier = context_identifier.strip('\"')
        self.pdp_type = pdp_type.strip('\"')
        self.ret_required = False

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.
        :return: String representation of command to send over connection to device.
        """
        return f"AT+CGDCONT={self.context_identifier},\"{self.pdp_type}\",\"{self.apn_name}\""


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

COMMAND_OUTPUT_default_parameter = """
AT+CGDCONT=1,"IPV4V6","5gkrk"

OK
"""

COMMAND_KWARGS_default_parameter = {"apn_name": "5gkrk"}

COMMAND_RESULT_default_parameter = {}


COMMAND_OUTPUT_all_parameter = """
AT+CGDCONT=4,"IP","5gkrk"

OK
"""

COMMAND_KWARGS_all_parameter = {
    "apn_name": "5gkrk",
    "context_identifier": "4",
    "pdp_type": "IP"
}

COMMAND_RESULT_all_parameter = {}
