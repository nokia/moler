# -*- coding: utf-8 -*-
"""
AT+GTIPPASS

AT commands specification:
google for: Fibocom AT command manual MBB V2.4
(always check against latest version of Fibocom AT command manual)
"""

__author__ = 'Jakub Kochaniak'
__copyright__ = 'Copyright (C) 2026, Nokia'
__email__ = 'jakub.kochaniak@nokia.com'

from moler.cmd.at.genericat import GenericAtCommand


class FibocomIpPassThrough(GenericAtCommand):
    """
    Command to enable IP pass-through. Example output:

    AT+GTIPPASS=1
    OK
    """
    class State:
        ENABLED = 1
        DISABLED = 0

    class Type:
        UNKNOWN = 0
        USB = 1
        ETHERNET = 2

    def __init__(self, state=State.DISABLED, conn_type=Type.UNKNOWN, mac: str = None, connection=None, prompt=None, newline_chars=None, runner=None):
        """
        Create instance of IpPassThrough class

        :param state: State of IP pass-through
        :param conn_type: Type of IP physical connection (USB or ETHERNET), when unknown, will be not used in command
        :param mac: MAC address of the device. Only required if type is Ethernet.
            The mac address corresponds to the mac address of the host client's Ethernet port.
        :param connection: Connection to the device
        :param prompt: Prompt to use for the command
        :param newline_chars: Newline characters to use for the command
        :param runner: Runner to use for the command
        """
        super(FibocomIpPassThrough, self).__init__(connection, operation="execute", prompt=prompt,
                                                   newline_chars=newline_chars, runner=runner)
        self.state = state
        self.conn_type = conn_type
        self.mac = mac or ""
        self.timeout = 180
        self.ret_required = False

    def build_command_string(self):
        if self.state == self.State.ENABLED:
            if self.conn_type == self.Type.USB:
                return f"AT+GTIPPASS={self.state},{self.conn_type}"
            elif self.conn_type == self.Type.ETHERNET:
                return f"AT+GTIPPASS={self.state},{self.conn_type},{self.mac}"
        return f"AT+GTIPPASS={self.state}"


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
COMMAND_OUTPUT_disable = """
AT+GTIPPASS=0
OK
"""

COMMAND_KWARGS_disable = {"state": 0}

COMMAND_RESULT_disable = {}


COMMAND_OUTPUT_enable_unknown = """
AT+GTIPPASS=1
OK
"""

COMMAND_KWARGS_enable_unknown = {"state": 1}

COMMAND_RESULT_enable_unknown = {}


COMMAND_OUTPUT_enable_usb = """
AT+GTIPPASS=1,1
OK
"""

COMMAND_KWARGS_enable_usb = {"state": 1, "conn_type": 1}

COMMAND_RESULT_enable_usb = {}


COMMAND_OUTPUT_enable_ethernet = """
AT+GTIPPASS=1,2,00:00:00:00:00:00
OK
"""

COMMAND_KWARGS_enable_ethernet = {"state": 1, "conn_type": 2, "mac": "00:00:00:00:00:00"}

COMMAND_RESULT_enable_ethernet = {}
