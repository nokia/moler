# -*- coding: utf-8 -*-
"""
Traceroute command module.
"""

__author__ = "Marcin Usielski"
__copyright__ = "Copyright (C) 2020, Nokia"
__email__ = "marcin.usielski@nokia.com"

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone
from moler.util.converterhelper import ConverterHelper


class Traceroute(GenericUnixCommand):
    def __init__(
        self,
        connection,
        destination,
        options=None,
        prompt=None,
        newline_chars=None,
        runner=None,
    ):
        """
        Traceroute command.
        :param connection: moler connection to device, terminal when command is executed.
        :param destination: address.
        :param options: options of traceroute command for unix.
        :param prompt: prompt on system where traceroute is executed.
        :param newline_chars: characters to split lines.
        :param runner: Runner to run command
        """
        super(Traceroute, self).__init__(
            connection=connection,
            prompt=prompt,
            newline_chars=newline_chars,
            runner=runner,
        )
        # Parameters defined by calling the command
        self.options = options
        self.destination = destination
        self._converter_helper = ConverterHelper.get_converter_helper()
        self.current_ret["hops"] = []

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.
        :return: String representation of command to send over connection to device.
        """
        cmd = "traceroute"
        if self.options:
            cmd = f"{cmd} {self.options}"
        cmd = f"{cmd} {self.destination}"
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Put your parsing code here.
        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: None
        """
        if is_full_line:
            try:
                self._parse_hop(line=line)
                self._parse_hop_address(line=line)
                self._parse_asterisks(line=line)
            except ParsingDone:
                pass  # line has been fully parsed by one of above parse-methods
        return super(Traceroute, self).on_new_line(line, is_full_line)

    #  1  gateway (10.0.2.2)  0.222 ms  0.191 ms  0.176 ms
    _re_hop = re.compile(
        r"(?P<HOP_NR>\d+)\s+(?P<NAME>\S+)\s+\((?P<ADDRESS>\S+)\)"
        r"\s+(?P<TTL1>\d+|\d+\.\d+)\s+(?P<TTL1_UNIT>\S+)"
        r"\s+(?P<TTL2>\d+|\d+\.\d+)\s+(?P<TTL2_UNIT>\S+)"
        r"\s+(?P<TTL3>\d+|\d+\.\d+)\s+(?P<TTL3_UNIT>\S+)"
    )

    def _parse_hop(self, line):
        """
        Parses packets from the line of command output
        :param line: Line of output of command.
        :return: None but raises ParsingDone if line has information to handle by this method.
        """
        if self._regex_helper.search_compiled(Traceroute._re_hop, line):
            hop = {}
            hop["nr"] = self._converter_helper.to_number(
                self._regex_helper.group("HOP_NR")
            )
            hop["name"] = self._regex_helper.group("NAME")
            hop["address"] = self._regex_helper.group("ADDRESS")
            hop["ttl1"] = self._converter_helper.to_number(
                self._regex_helper.group("TTL1")
            )
            hop["ttl1_unit"] = self._regex_helper.group("TTL1_UNIT")
            hop["ttl2"] = self._converter_helper.to_number(
                self._regex_helper.group("TTL2")
            )
            hop["ttl2_unit"] = self._regex_helper.group("TTL2_UNIT")
            hop["ttl3"] = self._converter_helper.to_number(
                self._regex_helper.group("TTL3")
            )
            hop["ttl3_unit"] = self._regex_helper.group("TTL3_UNIT")
            self.current_ret["hops"].append(hop)
            raise ParsingDone()

    #  1  10.0.2.2  0.222 ms  0.191 ms  0.176 ms
    _re_hop_address = re.compile(
        r"(?P<HOP_NR>\d+)\s+(?P<ADDRESS>\S+)"
        r"\s+(?P<TTL1>\d+|\d+\.\d+)\s+(?P<TTL1_UNIT>\S+)"
        r"\s+(?P<TTL2>\d+|\d+\.\d+)\s+(?P<TTL2_UNIT>\S+)"
        r"\s+(?P<TTL3>\d+|\d+\.\d+)\s+(?P<TTL3_UNIT>\S+)"
    )

    def _parse_hop_address(self, line):
        """
        Parses packets from the line of command output
        :param line: Line of output of command.
        :return: None but raises ParsingDone if line has information to handle by this method.
        """
        if self._regex_helper.search_compiled(Traceroute._re_hop_address, line):
            hop = {}
            hop["nr"] = self._converter_helper.to_number(
                self._regex_helper.group("HOP_NR")
            )
            hop["name"] = ""
            hop["address"] = self._regex_helper.group("ADDRESS")
            hop["ttl1"] = self._converter_helper.to_number(
                self._regex_helper.group("TTL1")
            )
            hop["ttl1_unit"] = self._regex_helper.group("TTL1_UNIT")
            hop["ttl2"] = self._converter_helper.to_number(
                self._regex_helper.group("TTL2")
            )
            hop["ttl2_unit"] = self._regex_helper.group("TTL2_UNIT")
            hop["ttl3"] = self._converter_helper.to_number(
                self._regex_helper.group("TTL3")
            )
            hop["ttl3_unit"] = self._regex_helper.group("TTL3_UNIT")
            self.current_ret["hops"].append(hop)
            raise ParsingDone()

    #  4  * * *
    _re_asterisks = re.compile(r"(?P<HOP_NR>\d+)\s+\*\s+\*\s+\*")

    def _parse_asterisks(self, line):
        """
        Parses packets from the line of command output
        :param line: Line of output of command.
        :return: None but raises ParsingDone if line has information to handle by this method.
        """
        if self._regex_helper.search_compiled(Traceroute._re_asterisks, line):
            hop = {}
            hop["nr"] = self._converter_helper.to_number(
                self._regex_helper.group("HOP_NR")
            )
            hop["name"] = ""
            hop["address"] = ""
            hop["ttl1"] = "*"
            hop["ttl1_unit"] = None
            hop["ttl2"] = "*"
            hop["ttl2_unit"] = None
            hop["ttl3"] = "*"
            hop["ttl3_unit"] = None
            self.current_ret["hops"].append(hop)
            raise ParsingDone()


COMMAND_OUTPUT = """
traceroute -m 5 192.168.8.1
traceroute to 192.168.8.1 (192.168.8.1), 30 hops max, 60 byte packets
 1  gateway (10.0.2.2)  0.295 ms  0.311 ms  0.292 ms
 2  gateway (10.0.2.2)  2.761 ms  3.141 ms  3.189 ms
 3  * * *
 4  10.3.3.3            0.295 ms  0.311 ms  0.292 ms
moler_bash# """
COMMAND_KWARGS = {"destination": "192.168.8.1", "options": "-m 5"}

COMMAND_RESULT = {
    "hops": [
        {
            "nr": 1,
            "name": "gateway",
            "address": "10.0.2.2",
            "ttl1": 0.295,
            "ttl1_unit": "ms",
            "ttl2": 0.311,
            "ttl2_unit": "ms",
            "ttl3": 0.292,
            "ttl3_unit": "ms",
        },
        {
            "nr": 2,
            "name": "gateway",
            "address": "10.0.2.2",
            "ttl1": 2.761,
            "ttl1_unit": "ms",
            "ttl2": 3.141,
            "ttl2_unit": "ms",
            "ttl3": 3.189,
            "ttl3_unit": "ms",
        },
        {
            "nr": 3,
            "name": "",
            "address": "",
            "ttl1": "*",
            "ttl1_unit": None,
            "ttl2": "*",
            "ttl2_unit": None,
            "ttl3": "*",
            "ttl3_unit": None,
        },
        {
            "nr": 4,
            "name": "",
            "address": "10.3.3.3",
            "ttl1": 0.295,
            "ttl1_unit": "ms",
            "ttl2": 0.311,
            "ttl2_unit": "ms",
            "ttl3": 0.292,
            "ttl3_unit": "ms",
        },
    ]
}
