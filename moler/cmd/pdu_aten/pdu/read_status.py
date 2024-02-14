# -*- coding: utf-8 -*-
"""
Command read status.
"""

import re

from moler.cmd.pdu_aten.pdu.generic_pdu import GenericPdu
from moler.exceptions import ParsingDone

__author__ = "Marcin Usielski"
__copyright__ = "Copyright (C) 2020, Nokia"
__email__ = "marcin.usielski@nokia.com"


class ReadStatus(GenericPdu):
    def __init__(
        self,
        connection,
        outlet,
        output_format=None,
        prompt=">",
        newline_chars=None,
        runner=None,
    ):
        """
        Class for command read status for PDU Aten device.

        :param connection: connection to device.
        :param outlet: outlet id.
        :param output_format: format of output. Maybe be None for simple format.
        :param prompt: expected prompt sending by device after command execution. Maybe String or compiled re.
        :param newline_chars:  new line chars on device (a list).
        :param runner: runner to run command.
        """
        super(ReadStatus, self).__init__(
            connection=connection,
            prompt=prompt,
            newline_chars=newline_chars,
            runner=runner,
        )
        self.outlet = outlet
        self.format = output_format

    def build_command_string(self):
        cmd = f"read status {self.outlet}"
        if self.format:
            cmd = f"{cmd} {self.format}"
        return cmd

    _outlet_id = "OUTLET"

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_outlet(line=line)
                self._parse_value(line=line)
            except ParsingDone:
                pass
        super(ReadStatus, self).on_new_line(line=line, is_full_line=is_full_line)

    # Outlet 01 on
    _re_outlet = re.compile(r"Outlet (?P<ID>\d+) (?P<VALUE>on|off)", re.IGNORECASE)

    def _parse_outlet(self, line):
        if self._regex_helper.search_compiled(ReadStatus._re_outlet, line):
            value = self._regex_helper.group("VALUE")
            if ReadStatus._outlet_id not in self.current_ret:
                self.current_ret[ReadStatus._outlet_id] = {}
            self.current_ret[ReadStatus._outlet_id][
                self._regex_helper.group("ID")
            ] = value
            self.current_ret["STATUS"] = value
            raise ParsingDone()

    # on
    _re_value = re.compile(r"(?P<VALUE>on|off)", re.IGNORECASE)

    def _parse_value(self, line):
        if self._regex_helper.search_compiled(ReadStatus._re_value, line):
            self.current_ret["STATUS"] = self._regex_helper.group("VALUE")
            raise ParsingDone()


COMMAND_OUTPUT = """read status o01 format
 Outlet 01 on

>"""

COMMAND_KWARGS = {
    "outlet": "o01",
    "output_format": "format",
}

COMMAND_RESULT = {
    "STATUS": "on",
    "OUTLET": {"01": "on"},
}

COMMAND_OUTPUT_simple = """read status o01
on

>"""

COMMAND_KWARGS_simple = {"outlet": "o01"}

COMMAND_RESULT_simple = {
    "STATUS": "on",
}
