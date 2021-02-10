# -*- coding: utf-8 -*-
"""
nft command module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2021, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone


class Nft(GenericUnixCommand):
    def __init__(self, connection, options=None, prompt=None, newline_chars=None, runner=None):
        super(Nft, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                  runner=runner)
        self.options = options
        self.ret_required = False
        self._filters = None
        self._set = None

    def build_command_string(self):
        cmd = "nft"
        if self.options:
            cmd = "{} {}".format(cmd, self.options)
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._find_open_bracket(line=line)
                self._find_close_bracket(line=line)
            except ParsingDone:
                pass
        return super(Nft, self).on_new_line(line, is_full_line)

    # table inet filter {
    _re_table_filter = re.compile(r"(\w+)\s+(\w+)\s+(\w+)\s*{")

    # set blackhole {
    _re_set = re.compile(r"(\w+)\s+(\w+)\s*{")

    def _find_open_bracket(self, line):
        if self._filters is None and self._regex_helper.search_compiled(Nft._re_table_filter, line):
            self._filters = [self._regex_helper.group(1), self._regex_helper.group(2), self._regex_helper.group(3)]
            raise ParsingDone()
        elif self._filters is not None and self._set is None and self._regex_helper.search_compiled(
                Nft._re_table_filter, line):
            self._set = [self._regex_helper.group(1), self._regex_helper.group(2)]
            raise ParsingDone()

    # }
    _re_close_bracket = re.compile(r"^\s*}\s*$")

    def _find_close_bracket(self, line):
        if self._regex_helper.search_compiled(Nft._re_close_bracket, line):
            if self._set is not None:
                self._set = None
            elif self._re_table_filter is not None:
                self._re_table_filter = None


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
}

chain forward {
    type filter hook forward priority 0; policy drop;
}

chain output {
    type filter hook output priority 0; policy accept;
}
}
user@server$"""

COMMAND_KWARGS = {
    'options': 'list table inet filter'
}

COMMAND_RESULT = {

}
