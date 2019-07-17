# -*- coding: utf-8 -*-
"""
SCPI command to support command without interesting output.
"""

from moler.cmd.scpi.scpi.genericscpistate import GenericScpiState
from moler.exceptions import CommandFailure
import re

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'marcin.usielski@nokia.com'


class RunCommand(GenericScpiState):

    def __init__(self, connection, command, error_regex=re.compile(r"ERROR", re.I), prompt=None,
                 newline_chars=None, runner=None):
        """
        Class for command CONF for SCPI device.

        :param connection: connection to device.
        :param command: string with command to send to device.
        :param error_regex: regex to fail the command.
        :param prompt: expected prompt sending by device after command execution. Maybe String or compiled re.
        :param newline_chars:  new line chars on device (a list).
        :param runner: runner to run command.
        """
        super(RunCommand, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                         runner=runner)
        self.command = command
        self.error_regex = error_regex
        self.ret_required = False

    def build_command_string(self):
        return self.command

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            if self.error_regex and self._regex_helper.search_compiled(self.error_regex, line):
                self.set_exception(CommandFailure(self, "Found error regex in line '{}'".format(line)))
        super(RunCommand, self).on_new_line(line, is_full_line)


COMMAND_OUTPUT_conf = """CONF:FREQ 1, (@1)
SCPI>"""

COMMAND_KWARGS_conf = {"command": "CONF:FREQ 1, (@1)"}

COMMAND_RESULT_conf = {}

COMMAND_OUTPUT_abs = """INP1:LEV1:ABS 1V
SCPI>"""

COMMAND_KWARGS_abs = {"command": "INP1:LEV1:ABS 1V"}

COMMAND_RESULT_abs = {}
