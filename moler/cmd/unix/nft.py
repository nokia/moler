# -*- coding: utf-8 -*-
"""
nft command module.
"""

__author__ = "Marcin Usielski"
__copyright__ = "Copyright (C) 2021, Nokia"
__email__ = "marcin.usielski@nokia.com"

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone
from moler.helpers import convert_to_number


class Nft(GenericUnixCommand):
    def __init__(
        self, connection, options=None, prompt=None, newline_chars=None, runner=None
    ):
        super(Nft, self).__init__(
            connection=connection,
            prompt=prompt,
            newline_chars=newline_chars,
            runner=runner,
        )
        self.options = options
        self.ret_required = False
        self._outer = None
        self._inner = None

    def build_command_string(self):
        cmd = "nft"
        if self.options:
            cmd = f"{cmd} {self.options}"
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_open_bracket(line=line)
                self._parse_close_bracket(line=line)
                self._parse_data_line(line=line)
            except ParsingDone:
                pass
        return super(Nft, self).on_new_line(line, is_full_line)

    # table inet filter {
    _begin_bracket = re.compile(r"^\s*(?P<KEY>\S.*\S|\S+)\s*{\s*$")

    def _parse_open_bracket(self, line):
        if self._regex_helper.search_compiled(Nft._begin_bracket, line):
            if self._outer is None:
                self._outer = self._regex_helper.group("KEY")
                self.current_ret[self._outer] = {}
                raise ParsingDone()
            elif self._inner is None:
                self._inner = self._regex_helper.group("KEY")
                self.current_ret[self._outer][self._inner] = {}
                raise ParsingDone()

    # }
    _re_close_bracket = re.compile(r"^\s*}\s*$")

    def _parse_close_bracket(self, line):
        if self._regex_helper.search_compiled(Nft._re_close_bracket, line):
            if self._inner is not None:
                self._inner = None
                raise ParsingDone()
            elif self._outer is not None:
                self._outer = None
                raise ParsingDone()

    _lines_key = "LINES"

    # type filter hook input priority 0; policy drop;
    _re_line = re.compile(r"^\s*(?P<CONTENT>\S.*\S|\S+)\s*$")

    def _parse_data_line(self, line):
        if self._inner is not None and self._regex_helper.search_compiled(
            self._re_line, line
        ):
            if Nft._lines_key not in self.current_ret[self._outer][self._inner]:
                self.current_ret[self._outer][self._inner][Nft._lines_key] = []
            self.current_ret[self._outer][self._inner][Nft._lines_key].append(
                self._regex_helper.group("CONTENT")
            )
            try:
                self._parse_two_values_with_type(line=line)
                self._parse_one_value(line=line)
            except ParsingDone:
                pass
            raise ParsingDone()

    # counter packets 0 bytes 0
    _re_two_values_with_type = re.compile(
        r"^\s*(?P<KIND>\S+)\s+(?P<KEY1>\S+)\s+(?P<VALUE1>\d+)\s+(?P<KEY2>\S+)\s+(?P<VALUE2>\d+)\s*$"
    )

    def _parse_two_values_with_type(self, line):
        if self._regex_helper.search_compiled(self._re_two_values_with_type, line):
            kind = self._regex_helper.group("KIND")
            if kind not in self.current_ret[self._outer][self._inner]:
                self.current_ret[self._outer][self._inner][kind] = {}
            self.current_ret[self._outer][self._inner][kind][
                self._regex_helper.group("KEY1")
            ] = convert_to_number(self._regex_helper.group("VALUE1"))
            self.current_ret[self._outer][self._inner][kind][
                self._regex_helper.group("KEY2")
            ] = convert_to_number(self._regex_helper.group("VALUE2"))
            raise ParsingDone()

    # type ipv4_addr
    _re_one_value = re.compile(r"^\s*(?P<KEY>\S+)\s+(?P<VALUE>\S+)\s*$")

    def _parse_one_value(self, line):
        if self._regex_helper.search_compiled(self._re_one_value, line):
            self.current_ret[self._outer][self._inner][
                self._regex_helper.group("KEY")
            ] = convert_to_number(self._regex_helper.group("VALUE"))
            raise ParsingDone()


COMMAND_OUTPUT = """nft list table inet filter
table inet filter {
set blackhole {
    type ipv4_addr
    size 65536
    flags timeout
}

chain input {
    type filter hook input priority 0; policy drop;
    ct state invalid drop
    ct state established,related accept
    iif "lo" accept
    ip6 nexthdr 58 icmpv6 type { destination-unreachable, packet-too-big, time-exceeded, parameter-problem, echo-request, echo-reply, mld-listener-query, mld-listener-report, mld-listener-done, nd-router-solicit, nd-router-advert, nd-neighbor-solicit, nd-neighbor-advert, ind-neighbor-solicit, ind-neighbor-advert, mld2-listener-report } accept
    ip protocol icmp icmp type { echo-reply, destination-unreachable, echo-request, router-advertisement, router-solicitation, time-exceeded, parameter-problem } accept
    ip saddr @blackhole counter packets 0 bytes 0 drop
    tcp flags syn tcp dport ssh meter flood { ip saddr timeout 1m limit rate over 10/second burst 5 packets}  set add ip saddr timeout 1m @blackhole drop
    tcp dport ssh accept
    counter packets 0 bytes 0
}

chain forward {
    type filter hook forward priority 0; policy drop;
}

chain output {
    type filter hook output priority 0; policy accept;
    counter packets 0 bytes 0
}
}
user@server$"""

COMMAND_KWARGS = {"options": "list table inet filter"}

COMMAND_RESULT = {
    "table inet filter": {
        "set blackhole": {
            "LINES": ["type ipv4_addr", "size 65536", "flags timeout"],
            "flags": "timeout",
            "size": 65536,
            "type": "ipv4_addr",
        },
        "chain input": {
            "LINES": [
                "type filter hook input priority 0; policy drop;",
                "ct state invalid drop",
                "ct state established,related accept",
                'iif "lo" accept',
                "ip6 nexthdr 58 icmpv6 type { destination-unreachable, packet-too-big, time-exceeded, parameter-problem, echo-request, echo-reply, mld-listener-query, mld-listener-report, mld-listener-done, nd-router-solicit, nd-router-advert, nd-neighbor-solicit, nd-neighbor-advert, ind-neighbor-solicit, ind-neighbor-advert, mld2-listener-report } accept",
                "ip protocol icmp icmp type { echo-reply, destination-unreachable, echo-request, router-advertisement, router-solicitation, time-exceeded, parameter-problem } accept",
                "ip saddr @blackhole counter packets 0 bytes 0 drop",
                "tcp flags syn tcp dport ssh meter flood { ip saddr timeout 1m limit rate over 10/second burst 5 packets}  set add ip saddr timeout 1m @blackhole drop",
                "tcp dport ssh accept",
                "counter packets 0 bytes 0",
            ],
            "counter": {"bytes": 0, "packets": 0},
        },
        "chain forward": {
            "LINES": ["type filter hook forward priority 0; policy drop;"]
        },
        "chain output": {
            "LINES": [
                "type filter hook output priority 0; policy accept;",
                "counter packets 0 bytes 0",
            ],
            "counter": {"bytes": 0, "packets": 0},
        },
    }
}
