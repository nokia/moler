# -*- coding: utf-8 -*-
"""
ip route command module.
"""

__author__ = "Yang Snackwell, Marcin Usielski, Grzegorz Latuszek"
__copyright__ = "Copyright (C) 2018-2019, Nokia"
__email__ = "snackwell.yang@nokia-sbell.com, marcin.usielski@nokia.com, grzegorz.latuszek@nokia.com"

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone
from moler.util.converterhelper import ConverterHelper


class IpRoute(GenericUnixCommand):
    """Unix command ip route"""

    def __init__(
        self,
        connection,
        prompt=None,
        newline_chars=None,
        runner=None,
        is_ipv6=False,
        addr_get=None,
        addr_from=None,
    ):
        """
        Unix command ip route.

        :param connection: Moler connection to device, terminal when command is executed.
        :param prompt: prompt (on system where command runs).
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        :param is_ipv6: Set True if IP v6 or False for IP v4.
        :param addr_get: Address get, parameter of unix ip route command.
        :param addr_from: From address, parameter of unix ip route command.
        """
        super(IpRoute, self).__init__(
            connection=connection,
            prompt=prompt,
            newline_chars=newline_chars,
            runner=runner,
        )
        self._converter_helper = ConverterHelper()
        # Parameters defined by calling the command
        self.is_ipv6 = is_ipv6
        self.addr_get = addr_get
        self.addr_from = addr_from
        self.current_ret["VIA"] = {}
        self.current_ret["ALL"] = []
        self.current_ret["ADDRESS"] = {}

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.

        :return: String representation of command to send over connection to device.
        """
        cmd = "ip route"
        if self.is_ipv6:
            cmd = "ip -6 route"
        if self.addr_get:
            cmd = f"{cmd} get {self.addr_get}"
            if self.addr_from:
                cmd = f"{cmd} from {self.addr_from}"
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Put your parsing code here.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise.
        :return: None
        """
        if is_full_line:
            try:
                self._parse_via_dev_proto_metric(line)
                self._parse_via_dev_proto_expires_mtu_hoplimit(line)
                self._parse_via_dev_metric_mtu(line)
                self._parse_via_dev_metric(line)
                self._parse_via_dev(line)
                self._parse_dev_proto_scope_src(line)
                self._parse_dev_proto_metric_mtu(line)
                self._parse_dev_proto_metric(line)
                self._parse_from_src_metric(line)
                self._parse_from_via_dev(line)
                self._parse_dev_src(line)
            except ParsingDone:
                pass  # line has been fully parsed by one of above parse-methods
        return super(IpRoute, self).on_new_line(line, is_full_line)

    def get_default_route(self):
        """
        Helpful method to find default route from command output.

        :return: Default route or None.
        """
        def_route = None
        if "VIA" in self.current_ret:
            if "default" in self.current_ret["VIA"]:
                def_route = self.current_ret["VIA"]["default"]["VIA"]

                for item in self.current_ret["ALL"]:
                    if "default" == item["ADDRESS"]:
                        if "METRIC" in item:
                            def_route = item["VIA"]

        return def_route

    def _process_line_address_all(self, line, regexp):
        """
        Method to process line.

        :param line: Line from device.
        :param regexp: Regexp to match.
        :return: None but raises ParsingDone if regex matches.
        """
        if self._regex_helper.search_compiled(regexp, line):
            _ret = {}
            _key_addr = self._regex_helper.group("ADDRESS")
            _ret[_key_addr] = self._regex_helper.groupdict()
            self.current_ret["ADDRESS"][_key_addr] = _ret[_key_addr]
            self.current_ret["ALL"].append(_ret[_key_addr])
            raise ParsingDone

    def _process_line_via_all(self, line, regexp):
        """
        Method to process line.

        :param line: Line from device.
        :param regexp: Regexp to match.
        :return: None but raises ParsingDone if regex matches.
        """
        if self._regex_helper.search_compiled(regexp, line):
            _ret = {}
            _key_addr = self._regex_helper.group("ADDRESS")
            _ret[_key_addr] = self._regex_helper.groupdict()
            self.current_ret["VIA"][_key_addr] = _ret[_key_addr]
            self.current_ret["ALL"].append(_ret[_key_addr])
            raise ParsingDone

    # default via fe80::a00:27ff:fe91:697c dev br0  proto ra  metric 1024  expires 1079sec mtu 1340 hoplimit 64
    _re_via_dev_proto_expires_mtu_hoplimit = re.compile(
        r"^\s*(?P<ADDRESS>\S+)\s+via\s+(?P<VIA>\S+)\s+"
        r"dev\s+(?P<DEV>\S+)\s+proto\s+(?P<PROTO>\S+)\s+"
        r"metric\s+(?P<METRIC>\S+)\s+expires\s+(?P<EXPIRES>\S+)\s+"
        r"mtu\s+(?P<MTU>\S+)\s+hoplimit\s+(?P<HOPLIMIT>\S+)$"
    )

    def _parse_via_dev_proto_expires_mtu_hoplimit(self, line):
        """
        Method to process line.

        :param line: Line from device.
        :return: None but raises ParsingDone if regex matches.
        """
        return self._process_line_via_all(
            line, IpRoute._re_via_dev_proto_expires_mtu_hoplimit
        )

    # default via 10.83.225.254 dev eth0  proto none  metric 1
    _re_via_dev_proto_metric = re.compile(
        r"^\s*(?P<ADDRESS>\S+)\s+via\s+(?P<VIA>\S+)\s+dev\s+(?P<DEV>\S+)\s+"
        r"proto\s+(?P<PROTO>\S+)\s+metric\s+(?P<METRIC>\S+)\s*$"
    )

    def _parse_via_dev_proto_metric(self, line):
        """
        Method to process line.

        :param line: Line from device.
        :return: None but raises ParsingDone if regex matches.
        """
        return self._process_line_via_all(line, IpRoute._re_via_dev_proto_metric)

    # default via 2a00:8a00:6000:7000:1000:4100:151:2 dev br0  metric 1  mtu 1500
    _re_via_dev_metric_mtu = re.compile(
        r"^\s*(?P<ADDRESS>\S+)\s+via\s+(?P<VIA>\S+)\s+dev\s+(?P<DEV>\S+)\s+"
        r"metric\s+(?P<METRIC>\S+)\s+mtu\s+(?P<MTU>\S+)\s*$"
    )

    def _parse_via_dev_metric_mtu(self, line):
        """
        Method to process line.

        :param line: Line from device.
        :return: None but raises ParsingDone if regex matches.
        """
        return self._process_line_via_all(line, IpRoute._re_via_dev_metric_mtu)

    # default via 2a00:8a00:6000:7000:a00:7900:3:0 dev br0.2605  metric 1
    _re_via_dev_metric = re.compile(
        r"^\s*(?P<ADDRESS>\S+)\s+via\s+(?P<VIA>\S+)\s+dev\s+(?P<DEV>\S+)\s+"
        r"metric\s+(?P<METRIC>\S+)\s*$"
    )

    def _parse_via_dev_metric(self, line):
        """
        Method to process line.

        :param line: Line from device.
        :return: None but raises ParsingDone if regex matches
        """
        return self._process_line_via_all(line, IpRoute._re_via_dev_metric)

    # default via 2a00:8a00:6000:7000:1000:4100:151:2 dev br0
    _re_via_dev = re.compile(
        r"^\s*(?P<ADDRESS>\S+)\s+via\s+(?P<VIA>\S+)\s+dev\s+(?P<DEV>\S+).*$"
    )

    def _parse_via_dev(self, line):
        """
        Method to process line.

        :param line: Line from device.
        :return: None but raises ParsingDone if regex matches.
        """
        return self._process_line_via_all(line, IpRoute._re_via_dev)

    # 10.83.224.0/23 dev eth0  proto kernel  scope link  src 10.83.225.103
    _re_dev_proto_scope_src = re.compile(
        r"^\s*(?P<ADDRESS>\S+)\s+dev\s+(?P<DEV>\S+)\s+"
        r"proto\s+(?P<PROTO>\S+)\s+scope\s+(?P<SCOPE>\S+)\s+src\s+(?P<SRC>\S+)\s*$"
    )

    def _parse_dev_proto_scope_src(self, line):
        """
        Method to process line.

        :param line: Line from device.
        :return: None but raises ParsingDone if regex matches.
        """
        return self._process_line_address_all(line, IpRoute._re_dev_proto_scope_src)

    # fe80::/64 dev br0  proto kernel  metric 256  mtu 1632
    _re_dev_proto_metric_mtu = re.compile(
        r"(?P<ADDRESS>\S+)\s+dev\s+(?P<DEV>\S+)\s+proto\s+(?P<PROTO>\S+)\s+"
        r"metric\s+(?P<METRIC>\S+)\s+mtu\s+(?P<MTU>\S+)"
    )

    def _parse_dev_proto_metric_mtu(self, line):
        """
        Method to process line.

        :param line: Line from device.
        :return: None but raises ParsingDone if regex matches.
        """
        return self._process_line_address_all(line, IpRoute._re_dev_proto_metric_mtu)

    # 2a00:8a00:6000:7000:a00:3900::/96 dev br0.2607  proto kernel  metric 256
    _re_dev_proto_metric = re.compile(
        r"(?P<ADDRESS>\S+)\s+dev\s+(?P<DEV>\S+)\s+proto\s+(?P<PROTO>\S+)\s+"
        r"metric\s+(?P<METRIC>\S+)"
    )

    def _parse_dev_proto_metric(self, line):
        """
        Method to process line.

        :param line: Line from device.
        :return: None but raises ParsingDone if regex matches.
        """
        return self._process_line_address_all(line, IpRoute._re_dev_proto_metric)

    # 2000::2011 from :: dev eth3  src 2000::2012  metric 0
    _re_from_src_metric = re.compile(
        r"(?P<ADDRESS>\S+)\s+from\s+(?P<FROM>\S+)\s+dev\s+(?P<DEV>\S+)\s+"
        r"src\s+(?P<SRC>\S+)\s+metric\s+(?P<METRIC>\d+)"
    )

    def _parse_from_src_metric(self, line):
        """
        Method to process line.

        :param line: Line from device.
        :return: None but raises ParsingDone if regex matches.
        """
        return self._process_line_address_all(line, IpRoute._re_from_src_metric)

    # ip route get 99.99.99.99 from 10.0.0.249
    # 99.99.99.99 from 10.0.0.249 via 10.0.0.2 dev br0
    _re_from_via_dev = re.compile(
        r"(?P<ADDRESS>\S+)\s+from\s+(?P<FROM>\S+)\s+via\s+(?P<VIA>\S+)\s+dev\s+(?P<DEV>\S+)"
    )

    def _parse_from_via_dev(self, line):
        """
        Method to process line.

        :param line: Line from device.
        :return: None but raises ParsingDone if regex matches.
        """
        return self._process_line_address_all(line, IpRoute._re_from_via_dev)

    # 10.0.0.249 dev eth3  src 10.0.0.2
    _re_dev_src = re.compile(
        r"(?P<ADDRESS>\S+)\s+dev\s+(?P<DEV>\S+)\s+src\s+(?P<SRC>\S+)"
    )

    def _parse_dev_src(self, line):
        """
        Method to process line.

        :param line: Line from device.
        :return: None but raises ParsingDone if regex matches.
        """
        return self._process_line_address_all(line, IpRoute._re_dev_src)


COMMAND_OUTPUT_ver_human = """
 host:~ # ip route
 default via 10.83.207.254 dev eth0  proto dhcp
 10.0.0.0/24 dev eth3  proto kernel  scope link  src 10.0.0.2
 10.1.52.248 via 10.0.0.248 dev eth3
 10.83.200.0/21 dev eth0  proto kernel  scope link  src 10.83.204.18
 10.83.224.0/23 via 10.89.5.126 dev eth2
 10.89.5.0/25 dev eth2  proto kernel  scope link  src 10.89.5.52
 10.254.0.0/16 via 10.89.5.126 dev eth2
 41.1.0.0/20 dev tunPGW  proto kernel  scope link  src 41.1.1.254
 192.168.255.0/24 dev eth1  proto kernel  scope link  src 192.168.255.126
 10.0.0.249 dev eth3  src 10.0.0.2
 host:~ # """

COMMAND_KWARGS_ver_human = {}

COMMAND_RESULT_ver_human = {
    "ADDRESS": {
        "10.0.0.0/24": {
            "ADDRESS": "10.0.0.0/24",
            "DEV": "eth3",
            "PROTO": "kernel",
            "SCOPE": "link",
            "SRC": "10.0.0.2",
        },
        "10.83.200.0/21": {
            "ADDRESS": "10.83.200.0/21",
            "DEV": "eth0",
            "PROTO": "kernel",
            "SCOPE": "link",
            "SRC": "10.83.204.18",
        },
        "10.89.5.0/25": {
            "ADDRESS": "10.89.5.0/25",
            "DEV": "eth2",
            "PROTO": "kernel",
            "SCOPE": "link",
            "SRC": "10.89.5.52",
        },
        "192.168.255.0/24": {
            "ADDRESS": "192.168.255.0/24",
            "DEV": "eth1",
            "PROTO": "kernel",
            "SCOPE": "link",
            "SRC": "192.168.255.126",
        },
        "41.1.0.0/20": {
            "ADDRESS": "41.1.0.0/20",
            "DEV": "tunPGW",
            "PROTO": "kernel",
            "SCOPE": "link",
            "SRC": "41.1.1.254",
        },
        "10.0.0.249": {"ADDRESS": "10.0.0.249", "DEV": "eth3", "SRC": "10.0.0.2"},
    },
    "ALL": [
        {"ADDRESS": "default", "DEV": "eth0", "VIA": "10.83.207.254"},
        {
            "ADDRESS": "10.0.0.0/24",
            "DEV": "eth3",
            "PROTO": "kernel",
            "SCOPE": "link",
            "SRC": "10.0.0.2",
        },
        {"ADDRESS": "10.1.52.248", "DEV": "eth3", "VIA": "10.0.0.248"},
        {
            "ADDRESS": "10.83.200.0/21",
            "DEV": "eth0",
            "PROTO": "kernel",
            "SCOPE": "link",
            "SRC": "10.83.204.18",
        },
        {"ADDRESS": "10.83.224.0/23", "DEV": "eth2", "VIA": "10.89.5.126"},
        {
            "ADDRESS": "10.89.5.0/25",
            "DEV": "eth2",
            "PROTO": "kernel",
            "SCOPE": "link",
            "SRC": "10.89.5.52",
        },
        {"ADDRESS": "10.254.0.0/16", "DEV": "eth2", "VIA": "10.89.5.126"},
        {
            "ADDRESS": "41.1.0.0/20",
            "DEV": "tunPGW",
            "PROTO": "kernel",
            "SCOPE": "link",
            "SRC": "41.1.1.254",
        },
        {
            "ADDRESS": "192.168.255.0/24",
            "DEV": "eth1",
            "PROTO": "kernel",
            "SCOPE": "link",
            "SRC": "192.168.255.126",
        },
        {"ADDRESS": "10.0.0.249", "DEV": "eth3", "SRC": "10.0.0.2"},
    ],
    "VIA": {
        "10.1.52.248": {"ADDRESS": "10.1.52.248", "DEV": "eth3", "VIA": "10.0.0.248"},
        "10.254.0.0/16": {
            "ADDRESS": "10.254.0.0/16",
            "DEV": "eth2",
            "VIA": "10.89.5.126",
        },
        "10.83.224.0/23": {
            "ADDRESS": "10.83.224.0/23",
            "DEV": "eth2",
            "VIA": "10.89.5.126",
        },
        "default": {"ADDRESS": "default", "DEV": "eth0", "VIA": "10.83.207.254"},
    },
}

COMMAND_OUTPUT_with_hoplimit = """
 host:~ # ip route
 default via fe80::a00:27ff:fe91:697c dev br0  proto ra  metric 1024  expires 1079sec mtu 1340 hoplimit 64
 host:~ # """

COMMAND_KWARGS_with_hoplimit = {}

COMMAND_RESULT_with_hoplimit = {
    "ADDRESS": {},
    "ALL": [
        {
            "ADDRESS": "default",
            "VIA": "fe80::a00:27ff:fe91:697c",
            "DEV": "br0",
            "PROTO": "ra",
            "METRIC": "1024",
            "EXPIRES": "1079sec",
            "MTU": "1340",
            "HOPLIMIT": "64",
        }
    ],
    "VIA": {
        "default": {
            "ADDRESS": "default",
            "VIA": "fe80::a00:27ff:fe91:697c",
            "DEV": "br0",
            "PROTO": "ra",
            "METRIC": "1024",
            "EXPIRES": "1079sec",
            "MTU": "1340",
            "HOPLIMIT": "64",
        }
    },
}

COMMAND_OUTPUT_with_metric = """
 host:~ # ip route
 default via 10.83.225.254 dev eth0  proto none  metric 1
 10.1.52.248 via 2a00:8a00:6000:7000:1000:4100:151:2 dev br0  metric 1  mtu 1500
 10.83.200.0/21 via 2a00:8a00:6000:7000:a00:7900:3:0 dev br0.2605  metric 1
 fe80::/64 dev br0  proto kernel  metric 256  mtu 1632
 2a00:8a00:6000:7000:a00:3900::/96 dev br0.2607  proto kernel  metric 256
 2000::2011 from :: dev eth3  src 2000::2012  metric 0
 host:~ # """

COMMAND_KWARGS_with_metric = {}

COMMAND_RESULT_with_metric = {
    "ADDRESS": {
        "fe80::/64": {
            "ADDRESS": "fe80::/64",
            "DEV": "br0",
            "METRIC": "256",
            "MTU": "1632",
            "PROTO": "kernel",
        },
        "2a00:8a00:6000:7000:a00:3900::/96": {
            "ADDRESS": "2a00:8a00:6000:7000:a00:3900::/96",
            "DEV": "br0.2607",
            "METRIC": "256",
            "PROTO": "kernel",
        },
        "2000::2011": {
            "ADDRESS": "2000::2011",
            "DEV": "eth3",
            "FROM": "::",
            "METRIC": "0",
            "SRC": "2000::2012",
        },
    },
    "ALL": [
        {
            "ADDRESS": "default",
            "VIA": "10.83.225.254",
            "DEV": "eth0",
            "PROTO": "none",
            "METRIC": "1",
        },
        {
            "ADDRESS": "10.1.52.248",
            "DEV": "br0",
            "METRIC": "1",
            "MTU": "1500",
            "VIA": "2a00:8a00:6000:7000:1000:4100:151:2",
        },
        {
            "ADDRESS": "10.83.200.0/21",
            "DEV": "br0.2605",
            "METRIC": "1",
            "VIA": "2a00:8a00:6000:7000:a00:7900:3:0",
        },
        {
            "ADDRESS": "fe80::/64",
            "DEV": "br0",
            "METRIC": "256",
            "MTU": "1632",
            "PROTO": "kernel",
        },
        {
            "ADDRESS": "2a00:8a00:6000:7000:a00:3900::/96",
            "DEV": "br0.2607",
            "METRIC": "256",
            "PROTO": "kernel",
        },
        {
            "ADDRESS": "2000::2011",
            "DEV": "eth3",
            "FROM": "::",
            "METRIC": "0",
            "SRC": "2000::2012",
        },
    ],
    "VIA": {
        "default": {
            "ADDRESS": "default",
            "VIA": "10.83.225.254",
            "DEV": "eth0",
            "PROTO": "none",
            "METRIC": "1",
        },
        "10.1.52.248": {
            "ADDRESS": "10.1.52.248",
            "DEV": "br0",
            "METRIC": "1",
            "MTU": "1500",
            "VIA": "2a00:8a00:6000:7000:1000:4100:151:2",
        },
        "10.83.200.0/21": {
            "ADDRESS": "10.83.200.0/21",
            "DEV": "br0.2605",
            "METRIC": "1",
            "VIA": "2a00:8a00:6000:7000:a00:7900:3:0",
        },
    },
}

COMMAND_OUTPUT_get = """host:~ # ip route get 10.0.2.0
broadcast 10.0.2.0 dev eth0 src 10.0.2.15
    cache <local,brd>
host:~ # """

COMMAND_KWARGS_get = {"addr_get": "10.0.2.0"}

COMMAND_RESULT_get = {
    "ADDRESS": {"10.0.2.0": {"ADDRESS": "10.0.2.0", "DEV": "eth0", "SRC": "10.0.2.15"}},
    "ALL": [{"ADDRESS": "10.0.2.0", "DEV": "eth0", "SRC": "10.0.2.15"}],
    "VIA": {},
}

COMMAND_OUTPUT_get_from = """host:~ # ip route get 10.0.2.0 from 10.0.2.15
broadcast 10.0.2.0 dev eth0 src 10.0.2.15
    cache <local,brd>
host:~ # """

COMMAND_KWARGS_get_from = {"addr_get": "10.0.2.0", "addr_from": "10.0.2.15"}

COMMAND_RESULT_get_from = {
    "ADDRESS": {"10.0.2.0": {"ADDRESS": "10.0.2.0", "DEV": "eth0", "SRC": "10.0.2.15"}},
    "ALL": [{"ADDRESS": "10.0.2.0", "DEV": "eth0", "SRC": "10.0.2.15"}],
    "VIA": {},
}
