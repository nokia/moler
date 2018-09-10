# -*- coding: utf-8 -*-
"""
Common part for all commands.

AT commands specification:
https://portal.3gpp.org/desktopmodules/Specifications/SpecificationDetails.aspx?specificationId=1515
(always check against latest version of standard)
"""

__author__ = 'Lukasz Blaszkiewicz, Kamil Kania, Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'kamil.kania@nokia.com, grzegorz.latuszek@nokia.com'

import re
from abc import abstractmethod

from moler.command import Command


class AtCommandModeNotSupported(Exception):
    pass


class AtCommandFailure(Exception):
    pass


class AtCmd(Command):
    def __init__(self, connection=None, operation="execute"):
        """
        Create instance of AtCmd class - base class for all AT commands
        :param connection: connection used to send command and receive its output
        :param operation: "execute", "read", "test" (not all AT commands support all modes)
        """
        if operation not in ["execute", "read", "test"]:
            raise AtCommandModeNotSupported("{} mode not supported for command".format(operation))
        self.operation = operation
        self.command_output = ''
        super(AtCmd, self).__init__(connection)

    def is_at_cmd_success(self):
        return "OK" in self.command_output

    def is_at_cmd_failure(self):
        return "ERROR" in self.command_output

    def data_received(self, data):
        """
        AT+<command_string>
        <information_response>
        <final_result_code>
        """
        self.command_output += data
        if self.is_at_cmd_success():
            self.parse_command_output()
        elif self.is_at_cmd_failure():
            self.parse_error_response()

    def parse_error_response(self):
        """
        When command itself is invalid or cannot be performed for some reason,
        or mobile termination error reporting is disabled:
        at+cmd
        ERROR

        When command was not processed due to an error related to MT operation:
        at+cmd
        +CME ERROR: result code
        """
        match = re.search(r'\n\+CME\s+ERROR:\s+(?P<error>[\w ]+)', self.command_output, flags=re.IGNORECASE)
        if match:
            self.set_exception(AtCommandFailure("ERROR: {}".format(match.group(1))))
        else:
            self.set_exception(AtCommandFailure("ERROR"))

    @abstractmethod
    def parse_command_output(self):
        """Should be used to parse specific AT command output and set result"""
        pass

    def set_at_command_string(self, command_base_string, execute_params=None):
        """
        Build full command-string of AT-cmd

        :param command_base_string: what AT command we run
        :param execute_params: list of (param, value) for operation 'execute'. Need list - order is important.
        :return: None
        """
        self.command_string = command_base_string
        if self.operation == 'test':
            self.command_string += "=?"
        elif self.operation == "read":
            self.command_string += "?"
        elif execute_params:
            params = ",".join(str(param_value) for param_name, param_value in execute_params if param_value or (param_value == 0))
            # param_value == 0  may generate valid AT-cmd like:
            # AT+CBST=0,0,0
            if params:
                self.command_string += "=" + params
