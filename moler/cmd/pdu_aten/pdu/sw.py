# -*- coding: utf-8 -*-
"""
Command sw.
"""

from moler.cmd.pdu_aten.pdu.generic_pdu import GenericPdu

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'marcin.usielski@nokia.com'


class Sw(GenericPdu):

    def __init__(self, connection, outlet, control, option=None, prompt=">", newline_chars=None, runner=None):
        """
        Class for command read meter for PDU Aten device.

        :param connection: connection to device.
        :param outlet: outlet id.
        :param control: value of control (for example: on, off or reboot).
        :param option: value for option (for example: imme or delay).
        :param prompt: expected prompt sending by device after command execution. Maybe String or compiled re.
        :param newline_chars:  new line chars on device (a list).
        :param runner: runner to run command.
        """
        super(Sw, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                 runner=runner)
        self.outlet = outlet
        self.control = control
        self.option = option
        self.ret_required = False

    def build_command_string(self):
        cmd = "sw {} {}".format(self.outlet, self.control)
        if self.option:
            cmd = "{} {}".format(cmd, self.option)
        return cmd


COMMAND_OUTPUT_reboot = """sw o01 reboot
 Outlet<01> command is setting

>"""

COMMAND_KWARGS_reboot = {
    "outlet": "o01",
    "control": "reboot"
}

COMMAND_RESULT_reboot = {
}


COMMAND_OUTPUT_on = """sw o01 on
 Outlet<01> command is setting

>"""

COMMAND_KWARGS_on = {
    "outlet": "o01",
    "control": "on"
}

COMMAND_RESULT_on = {
}

COMMAND_OUTPUT_off = """sw o01 off imme
 Outlet<01> command is setting

>"""

COMMAND_KWARGS_off = {
    "outlet": "o01",
    "control": "off",
    "option": "imme"
}

COMMAND_RESULT_off = {
}
