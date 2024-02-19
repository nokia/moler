# -*- coding: utf-8 -*-
"""
ip addr command module.
"""

__author__ = "Sylwester Golonka"
__copyright__ = "Copyright (C) 2018, Nokia"
__email__ = "sylwester.golonka@nokia.com"

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone


class IpNeigh(GenericUnixCommand):
    def __init__(
        self, connection, options=None, prompt=None, newline_chars=None, runner=None
    ):
        super(IpNeigh, self).__init__(
            connection=connection,
            prompt=prompt,
            newline_chars=newline_chars,
            runner=runner,
        )
        self.options = options
        self.ret_required = False

    def build_command_string(self):
        cmd = "ip neigh"
        if self.options:
            cmd = f"{cmd} {self.options}"
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_line(line)
            except ParsingDone:
                pass
        return super(IpNeigh, self).on_new_line(line, is_full_line)

    _re_parse = re.compile(r"(?P<IP>.*)\s.*\s(?P<DEV>.*)\s.*\s(?P<MAC>.*)\s(?P<NUD>.*)")

    def _parse_line(self, line):
        if self._regex_helper.search_compiled(IpNeigh._re_parse, line):
            self.current_ret[self._regex_helper.group("IP")] = {}
            self.current_ret[self._regex_helper.group("IP")][
                "MAC"
            ] = self._regex_helper.group("MAC")
            self.current_ret[self._regex_helper.group("IP")][
                "DEV"
            ] = self._regex_helper.group("DEV")
            self.current_ret[self._regex_helper.group("IP")][
                "NUD"
            ] = self._regex_helper.group("NUD")
            raise ParsingDone


COMMAND_OUTPUT = """
root@fzm-lsp-k2:~# ip neigh show
0.83.200.2 dev eth0 lladdr 00:50:56:95:09:24 STALE
10.83.200.30 dev eth0 lladdr 00:50:56:b6:65:f9 STALE
192.168.255.16 dev LMT_153 lladdr b4:99:4c:b3:90:65 STALE
192.168.255.245 dev LMT_153  FAILED
10.89.0.248 dev eth0 lladdr 2c:44:fd:20:9e:39 STALE
10.1.101.153 dev TRS_153 lladdr 60:a8:fe:78:30:22 REACHABLE
10.83.205.180 dev eth0 lladdr 08:00:27:1a:c9:d9 STALE
10.83.200.190 dev eth0 lladdr 00:90:e8:0d:dd:7b STALE
10.83.204.159 dev eth0 lladdr c4:34:6b:59:68:4d STALE
10.83.200.183 dev eth0 lladdr 00:90:e8:0f:c7:57 STALE
10.83.206.133 dev eth0 lladdr 2c:44:fd:23:0e:8f STALE
192.168.255.129 dev LMT_153 lladdr b4:99:4c:b3:90:65 REACHABLE
10.83.205.250 dev eth0 lladdr 00:25:b3:d2:8f:08 STALE
10.83.207.237 dev eth0 lladdr 00:30:64:17:9b:54 STALE
10.83.207.254 dev eth0 lladdr 84:c1:c1:c3:04:00 DELAY
10.83.200.250 dev eth0 lladdr 00:50:56:95:8a:d9 REACHABLE
10.83.201.230 dev eth0 lladdr cc:e1:7f:87:d8:ff STALE
10.83.200.255 dev eth0 lladdr 00:50:56:95:7e:d2 STALE
10.83.200.195 dev eth0 lladdr 00:90:e8:0d:dd:7c STALE
10.89.5.25 dev eth3 lladdr 08:00:27:f7:f7:95 STALE
10.83.206.60 dev eth0 lladdr 40:a8:f0:54:69:1e STALE
10.83.200.37 dev eth0 lladdr 00:50:56:95:4b:7d STALE
fe80::250:56ff:fe95:abf1 dev eth0 lladdr 00:50:56:95:ab:f1 STALE
fe80::250:56ff:fe95:257c dev eth0 lladdr 00:50:56:95:25:7c STALE
fe80::2cd8:123:46b1:3fdd dev eth0 lladdr 88:51:fb:5e:e9:49 STALE
fe80::20f:feff:fec6:17a0 dev eth0 lladdr 00:0f:fe:c6:17:a0 STALE
fe80::f59f:193e:a283:f168 dev eth0 lladdr 40:a8:f0:65:be:e3 STALE
fe80::250:56ff:fe95:2ef6 dev eth0 lladdr 00:50:56:95:2e:f6 STALE
fe80::6a05:caff:fe2d:abb9 dev eth3 lladdr 68:05:ca:2d:ab:b9 STALE
fe80::250:56ff:fe95:e110 dev eth0 lladdr 00:50:56:95:e1:10 STALE
fe80::250:56ff:fe95:c9e7 dev eth0 lladdr 00:50:56:95:c9:e7 STALE
root@fzm-lsp-k2:~# """

COMMAND_KWARGS = {"options": "show"}
COMMAND_RESULT = {
    "0.83.200.2": {"DEV": "eth0", "MAC": "00:50:56:95:09:24", "NUD": "STALE"},
    "10.1.101.153": {"DEV": "TRS_153", "MAC": "60:a8:fe:78:30:22", "NUD": "REACHABLE"},
    "10.83.200.183": {"DEV": "eth0", "MAC": "00:90:e8:0f:c7:57", "NUD": "STALE"},
    "10.83.200.190": {"DEV": "eth0", "MAC": "00:90:e8:0d:dd:7b", "NUD": "STALE"},
    "10.83.200.195": {"DEV": "eth0", "MAC": "00:90:e8:0d:dd:7c", "NUD": "STALE"},
    "10.83.200.250": {"DEV": "eth0", "MAC": "00:50:56:95:8a:d9", "NUD": "REACHABLE"},
    "10.83.200.255": {"DEV": "eth0", "MAC": "00:50:56:95:7e:d2", "NUD": "STALE"},
    "10.83.200.30": {"DEV": "eth0", "MAC": "00:50:56:b6:65:f9", "NUD": "STALE"},
    "10.83.200.37": {"DEV": "eth0", "MAC": "00:50:56:95:4b:7d", "NUD": "STALE"},
    "10.83.201.230": {"DEV": "eth0", "MAC": "cc:e1:7f:87:d8:ff", "NUD": "STALE"},
    "10.83.204.159": {"DEV": "eth0", "MAC": "c4:34:6b:59:68:4d", "NUD": "STALE"},
    "10.83.205.180": {"DEV": "eth0", "MAC": "08:00:27:1a:c9:d9", "NUD": "STALE"},
    "10.83.205.250": {"DEV": "eth0", "MAC": "00:25:b3:d2:8f:08", "NUD": "STALE"},
    "10.83.206.133": {"DEV": "eth0", "MAC": "2c:44:fd:23:0e:8f", "NUD": "STALE"},
    "10.83.206.60": {"DEV": "eth0", "MAC": "40:a8:f0:54:69:1e", "NUD": "STALE"},
    "10.83.207.237": {"DEV": "eth0", "MAC": "00:30:64:17:9b:54", "NUD": "STALE"},
    "10.83.207.254": {"DEV": "eth0", "MAC": "84:c1:c1:c3:04:00", "NUD": "DELAY"},
    "10.89.0.248": {"DEV": "eth0", "MAC": "2c:44:fd:20:9e:39", "NUD": "STALE"},
    "10.89.5.25": {"DEV": "eth3", "MAC": "08:00:27:f7:f7:95", "NUD": "STALE"},
    "192.168.255.129": {
        "DEV": "LMT_153",
        "MAC": "b4:99:4c:b3:90:65",
        "NUD": "REACHABLE",
    },
    "192.168.255.16": {"DEV": "LMT_153", "MAC": "b4:99:4c:b3:90:65", "NUD": "STALE"},
    "fe80::20f:feff:fec6:17a0": {
        "DEV": "eth0",
        "MAC": "00:0f:fe:c6:17:a0",
        "NUD": "STALE",
    },
    "fe80::250:56ff:fe95:257c": {
        "DEV": "eth0",
        "MAC": "00:50:56:95:25:7c",
        "NUD": "STALE",
    },
    "fe80::250:56ff:fe95:2ef6": {
        "DEV": "eth0",
        "MAC": "00:50:56:95:2e:f6",
        "NUD": "STALE",
    },
    "fe80::250:56ff:fe95:abf1": {
        "DEV": "eth0",
        "MAC": "00:50:56:95:ab:f1",
        "NUD": "STALE",
    },
    "fe80::250:56ff:fe95:c9e7": {
        "DEV": "eth0",
        "MAC": "00:50:56:95:c9:e7",
        "NUD": "STALE",
    },
    "fe80::250:56ff:fe95:e110": {
        "DEV": "eth0",
        "MAC": "00:50:56:95:e1:10",
        "NUD": "STALE",
    },
    "fe80::2cd8:123:46b1:3fdd": {
        "DEV": "eth0",
        "MAC": "88:51:fb:5e:e9:49",
        "NUD": "STALE",
    },
    "fe80::6a05:caff:fe2d:abb9": {
        "DEV": "eth3",
        "MAC": "68:05:ca:2d:ab:b9",
        "NUD": "STALE",
    },
    "fe80::f59f:193e:a283:f168": {
        "DEV": "eth0",
        "MAC": "40:a8:f0:65:be:e3",
        "NUD": "STALE",
    },
}
