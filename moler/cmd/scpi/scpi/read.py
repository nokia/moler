# -*- coding: utf-8 -*-
"""
SCPI command READ.
"""

import re
from moler.cmd.scpi.scpi.genericscpistate import GenericScpiState

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'marcin.usielski@nokia.com'


class Read(GenericScpiState):

    def __init__(self, connection, prompt=None, newline_chars=None, runner=None):
        """
        Class for command READ for SCPI device.

        :param connection: connection to device.
        :param prompt: expected prompt sending by device after command execution. Maybe String or compiled re.
        :param newline_chars:  new line chars on device (a list).
        :param runner: runner to run command.
        """
        super(Read, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                   runner=runner)

    def build_command_string(self):
        return "READ?"

    # +8.59803192358089E-005
    _re_value = re.compile(r"(?P<VALUE>[+\-]?\d+\.\d+([eE][+\-]\d+))")

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            if self._regex_helper.search_compiled(self._re_value, line):
                self.current_ret['VALUE_RAW'] = self._regex_helper.group("VALUE")
                self.current_ret['VALUE_FLOAT'] = float(self._regex_helper.group("VALUE"))
        super(Read, self).on_new_line(line=line, is_full_line=is_full_line)


COMMAND_OUTPUT = """READ?
+8.59803192358089E-005
SCPI>"""

COMMAND_KWARGS = {}

COMMAND_RESULT = {
    "VALUE_RAW": '+8.59803192358089E-005',
    "VALUE_FLOAT": 8.59803192358089E-5,
}
