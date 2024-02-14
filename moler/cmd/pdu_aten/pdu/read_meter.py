# -*- coding: utf-8 -*-
"""
Command read status.
"""

import re
from moler.cmd.pdu_aten.pdu.generic_pdu import GenericPdu
from moler.exceptions import ParsingDone
from moler.util.converterhelper import ConverterHelper

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'marcin.usielski@nokia.com'


class ReadMeter(GenericPdu):

    def __init__(self, connection, target, measurement, outlet=None, output_format=None, prompt=">", newline_chars=None, runner=None):
        """
        Class for command read meter for PDU Aten device.

        :param connection: connection to device.
        :param outlet: outlet id.
        :param output_format: format of output. Maybe be None for simple format.
        :param prompt: expected prompt sending by device after command execution. Maybe String or compiled re.
        :param newline_chars:  new line chars on device (a list).
        :param runner: runner to run command.
        """
        super(ReadMeter, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                        runner=runner)
        self.outlet = outlet
        self.format = output_format
        self.target = target
        self.measurement = measurement
        self._converter_helper = ConverterHelper.get_converter_helper()

    def build_command_string(self):
        cmd = f"read meter {self.target}"
        if self.outlet:
            cmd = f"{cmd} {self.outlet}"
        cmd = f"{cmd} {self.measurement}"
        if self.format:
            cmd = f"{cmd} {self.format}"
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_value(line=line)
            except ParsingDone:
                pass
        super(ReadMeter, self).on_new_line(line=line, is_full_line=is_full_line)

    # V:233.13
    _re_value = re.compile(r"(?P<TYPE>\w*)\s*:?\s*(?P<VALUE>[\d\.]+)", re.IGNORECASE)

    def _parse_value(self, line):
        if self._regex_helper.search_compiled(ReadMeter._re_value, line):
            value_raw = self._regex_helper.group("VALUE")
            self.current_ret['TYPE'] = self._regex_helper.group("TYPE")
            self.current_ret["VALUE_RAW"] = value_raw
            self.current_ret["VALUE"] = self._converter_helper.to_number(value_raw)
            raise ParsingDone()


COMMAND_OUTPUT = """read meter dev volt
 V:233.03

>"""

COMMAND_KWARGS = {
    "target": "dev",
    "measurement": "volt"
}

COMMAND_RESULT = {
    'TYPE': 'V',
    'VALUE_RAW': '233.03',
    'VALUE': 233.03
}

COMMAND_OUTPUT_simple = """read meter olt o01 volt simple
 233.40

>"""

COMMAND_KWARGS_simple = {
    "target": "olt",
    "outlet": "o01",
    "measurement": "volt",
    "output_format": "simple",
}

COMMAND_RESULT_simple = {
    'TYPE': '',
    'VALUE_RAW': '233.40',
    'VALUE': 233.40
}
