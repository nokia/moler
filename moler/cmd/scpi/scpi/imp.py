# -*- coding: utf-8 -*-
"""
SCPI command IMP module.
"""

from moler.cmd.scpi.scpi.genricscpinooutput import GenericScpiNoOutput

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'marcin.usielski@nokia.com'


class Imp(GenericScpiNoOutput):

    def __init__(self, connection, input_port, prompt=None, newline_chars=None, runner=None, params=None):
        """
        Class for command IMP (impedance) for SCPI device.

        :param connection: connection to device.
        :param input_port: port on device to use.
        :param prompt: expected prompt sending by device after command execution. Maybe String or compiled re.
        :param newline_chars:  new line chars on device (a list).
        :param runner: runner to run command.
        :param params: parameters to add to command string.
        """
        super(Imp, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                   runner=runner)
        self.params = params
        self.input_port = input_port

    def build_command_string(self):
        cmd = "{}:IMP".format(self.input_port)
        if self.params:
            cmd = "{} {}".format(cmd, self.params)
        return cmd


COMMAND_OUTPUT_param = """INP1:IMP 50
SCPI>"""

COMMAND_KWARGS_param = {"params": 50, "input_port": 'INP1'}

COMMAND_RESULT_param = {}
