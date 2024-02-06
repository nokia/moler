# -*- coding: utf-8 -*-
"""
SCPI command idn module.
"""


from moler.cmd.scpi.scpi.genericscpistate import GenericScpiState

__author__ = "Marcin Usielski"
__copyright__ = "Copyright (C) 2019, Nokia"
__email__ = "marcin.usielski@nokia.com"


class Idn(GenericScpiState):
    def __init__(self, connection, prompt=None, newline_chars=None, runner=None):
        """
        Class for command IDN for SCPI device.

        :param connection: connection to device.
        :param prompt: expected prompt sending by device after command execution. Maybe String or compiled re.
        :param newline_chars:  new line chars on device (a list).
        :param runner: runner to run command.
        """
        super(Idn, self).__init__(
            connection=connection,
            prompt=prompt,
            newline_chars=newline_chars,
            runner=runner,
        )
        self.current_ret["RAW_OUTPUT"] = []

    def build_command_string(self):
        return "*idn?"

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            self.current_ret["RAW_OUTPUT"].append(line)
        return super(Idn, self).on_new_line(line=line, is_full_line=is_full_line)


COMMAND_OUTPUT = """*idn?
Agilent Technologies,N9020A,MY53420262,A.13.15
SCPI>"""

COMMAND_KWARGS = {}

COMMAND_RESULT = {"RAW_OUTPUT": ["Agilent Technologies,N9020A,MY53420262,A.13.15"]}
