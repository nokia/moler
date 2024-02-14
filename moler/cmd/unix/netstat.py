# -*- coding: utf-8 -*-
__author__ = "Mateusz Szczurek, Michal Ernst"
__copyright__ = "Copyright (C) 2019, Nokia"
__email__ = "mateusz.m.szczurek@nokia.com, michal.ernst@nokia.com"

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone
from moler.helpers import convert_to_number


class Netstat(GenericUnixCommand):
    """Netstat command class."""

    def __init__(
        self, connection, options="", prompt=None, newline_chars=None, runner=None
    ):
        """
        Netstat command.

        :param connection: Moler connection to device, terminal when command is executed.
        :param options: Options of netstat command.
        :param prompt: Expected prompt that has been sent by device after command execution.
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        """
        super(Netstat, self).__init__(
            connection=connection,
            prompt=prompt,
            newline_chars=newline_chars,
            runner=runner,
        )
        # Parameters defined by calling the command
        self.options = options
        self._active = ""
        self.statistics_proto = ""

    def build_command_string(self):
        """
        Build command string from parameters passed to object.

        :return: String representation of the command to send over a connection to the device.
        """
        if self.options:
            cmd = f"netstat {self.options}"
        else:
            cmd = "netstat"
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Put your parsing code here.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: None
        """
        try:
            if is_full_line:
                self._parse_active(line)
                self._parse_headers_unix(line)
                self._parse_headers_internet(line)
                self._parse_interface(line)
                self._parse_groups(line)
                self._parse_routing_table(line)
                self._parse_statistics(line)
        except ParsingDone:
            pass  # line has been fully parsed by one of above parse-methods
        return super(Netstat, self).on_new_line(line, is_full_line)

    # Active UNIX domain sockets (w/o servers)
    _re_active = re.compile(
        r"Active\s*(?P<ACTIVE>.*) \s*\((w/o servers|servers and established)\)"
    )

    def _parse_active(self, line):
        """
        Parse active connections or sockets in line. Set self._active to current type of connection.

        :param line: Line to process.
        :return: None but raises ParsingDone if line has the information to handle by this method.
        """
        if self._regex_helper.search_compiled(Netstat._re_active, line):
            self._active = self._regex_helper.group("ACTIVE")
            raise ParsingDone

    # unix  2      [ ]         DGRAM                    15382    /var/cache/samba/msg/950
    _re_header_unix = re.compile(
        r"(?P<PROTO>\S*)\s+(?P<REFCNT>\d*)\s+(?P<FLAGS>\[.*\])\s+(?P<TYPE>[A-Z]*)\s+(?P<STATE>[A-Z]*)?\s+(?P<INODE>\d*)"
        r"\s*(?P<PID>\d+/\S+|-)?\s+(?P<PATH>\S*)"
    )

    def _parse_headers_unix(self, line):
        """
        Check if parsed type of connection is a UNIX domain socket. If yes then parse corresponding values in line.
        Append those values to UNIX_SOCKETS list.

        :param line: Line to process.
        :return: None but raises ParsingDone if line has the information to handle by this method.
        """
        if self._active == "UNIX domain sockets":
            if "UNIX_SOCKETS" not in self.current_ret:
                self.current_ret["UNIX_SOCKETS"] = []
            if self._regex_helper.search_compiled(Netstat._re_header_unix, line):
                _ret_dict = {
                    "proto": self._regex_helper.group("PROTO"),
                    "refcnt": convert_to_number(self._regex_helper.group("REFCNT")),
                    "flags": self._regex_helper.group("FLAGS"),
                    "type": self._regex_helper.group("TYPE"),
                    "state": self._regex_helper.group("STATE"),
                    "i-node": convert_to_number(self._regex_helper.group("INODE")),
                    "path": self._regex_helper.group("PATH"),
                }
                if self._regex_helper.group("PID"):
                    _ret_dict.update(
                        {"pid/program name": self._regex_helper.group("PID")}
                    )
                self.current_ret["UNIX_SOCKETS"].append(_ret_dict)
                raise ParsingDone

    # tcp6       1      0 localhost:34256         localhost:ipp           CLOSE_WAIT
    _re_header_internet = re.compile(
        r"(?P<PROTO>\S+)\s{1,10}(?P<RECVQ>\d+)?\s*(?P<SENDQ>\d+)?\s*(?P<LADDRESS>\S+:\S+)\s+(?P<FADDRESS>\S+:\S+)"
        r"?\s+(?P<STATE>\S+)\s*(?P<PID>\d+/\S+|-)?"
    )

    def _parse_headers_internet(self, line):
        """
        Check if parsed type of connection is an internet type. If yes then parse corresponding values in line.
        Append those values to INTERNET_CONNECTIONS list.

        :param line: Line to process.
        :return: None but raises ParsingDone if line has the information to handle by this method.
        """
        if self._active == "Internet connections":
            if "INTERNET_CONNECTIONS" not in self.current_ret:
                self.current_ret["INTERNET_CONNECTIONS"] = []
            if self._regex_helper.search_compiled(Netstat._re_header_internet, line):
                _ret_dict = {
                    "proto": self._regex_helper.group("PROTO"),
                    "recv-q": convert_to_number(self._regex_helper.group("RECVQ")),
                    "send-q": convert_to_number(self._regex_helper.group("SENDQ")),
                    "local address": self._regex_helper.group("LADDRESS"),
                    "foreign address": self._regex_helper.group("FADDRESS"),
                    "state": self._regex_helper.group("STATE"),
                }
                if self._regex_helper.group("PID"):
                    _ret_dict.update(
                        {"pid/program name": self._regex_helper.group("PID")}
                    )
                self.current_ret["INTERNET_CONNECTIONS"].append(_ret_dict)
                raise ParsingDone

    # lo              1      all-systems.mcast.net
    _re_groups = re.compile(r"(?P<INTERFACE>\S*)\s+(?P<REFCNT>\d*)\s+(?P<GROUP>\S*$)")

    def _parse_groups(self, line):
        """
        Check if -g paramter is in use. If yes then parse corresponding values in line.
        Append those values to GROUP list.

        :param line: Line to process.
        :return: None but raises ParsingDone if line has the information to handle by this method.
        """
        if "g" in self.options and self._regex_helper.search_compiled(
            Netstat._re_groups, line
        ):
            if "GROUP" not in self.current_ret:
                self.current_ret["GROUP"] = []
            _ret_dict = {
                "interface": self._regex_helper.group("INTERFACE"),
                "refcnt": convert_to_number(self._regex_helper.group("REFCNT")),
                "group": self._regex_helper.group("GROUP"),
            }
            self.current_ret["GROUP"].append(_ret_dict)
            raise ParsingDone

    # eth0       1500 0    178226      0      0 0          1417      0      0      0 BMRU
    _re_interface = re.compile(
        r"(?P<INTERFACE>\S*)\s+(?P<MTU>\d*)\s+(?P<MET>\d*)\s+(?P<RXOK>\d*)\s+(?P<RXERR>\d*)\s+(?P<RXDRP>\d*)"
        r"\s+(?P<RXOVR>\d*)\s+(?P<TXOK>\d*)\s+(?P<TXERR>\d*)\s+(?P<TXDRP>\d*)\s+(?P<TXOVR>\d*)\s+(?P<FLG>\S*)"
    )

    def _parse_interface(self, line):
        """
        Check if -i paramter is in use. If yes then parse corresponding values in line.
        Append those values to INTERFACE list.

        :param line: Line to process.
        :return: None but raises ParsingDone if line has the information to handle by this method.
        """
        if "i" in self.options and self._regex_helper.search_compiled(
            Netstat._re_interface, line
        ):
            if "INTERFACE" not in self.current_ret:
                self.current_ret["INTERFACE"] = []
            _ret_dict = {
                "iface": self._regex_helper.group("INTERFACE"),
                "mtu": convert_to_number(self._regex_helper.group("MTU")),
                "met": convert_to_number(self._regex_helper.group("MET")),
                "rx-ok": convert_to_number(self._regex_helper.group("RXOK")),
                "rx-err": convert_to_number(self._regex_helper.group("RXERR")),
                "rx-drp": convert_to_number(self._regex_helper.group("RXDRP")),
                "rx-ovr": convert_to_number(self._regex_helper.group("RXOVR")),
                "tx-ok": convert_to_number(self._regex_helper.group("TXOK")),
                "tx-err": convert_to_number(self._regex_helper.group("TXERR")),
                "tx-drp": convert_to_number(self._regex_helper.group("TXDRP")),
                "tx-ovr": convert_to_number(self._regex_helper.group("TXOVR")),
                "flg": self._regex_helper.group("FLG"),
            }
            self.current_ret["INTERFACE"].append(_ret_dict)
            raise ParsingDone

    # default         123.123.123.123  0.0.0.0         UG        0 0          0 eth0
    _re_routing_table = re.compile(
        r"(?P<DESTINATION>\S*)\s+(?P<GATEWAY>\S*)\s+(?P<GENMASK>\S*)\s+(?P<FLAGS>[A-Z]*)\s+(?P<MSS>\d*)"
        r"\s+(?P<WINDOW>\d*)\s+(?P<IRTT>\d*)\s+(?P<INTERFACE>\S*)$"
    )

    def _parse_routing_table(self, line):
        """
        Check if -r paramter is in use. If yes then parse corresponding values in line.
        Append those values to GROUP list.

        :param line: Line to process.
        :return: None but raises ParsingDone if line has the information to handle by this method.
        """
        if "r" in self.options and self._regex_helper.search_compiled(
            Netstat._re_routing_table, line
        ):
            if "ROUTING_TABLE" not in self.current_ret:
                self.current_ret["ROUTING_TABLE"] = []
            _ret_dict = {
                "destination": self._regex_helper.group("DESTINATION"),
                "gateway": self._regex_helper.group("GATEWAY"),
                "genmask": self._regex_helper.group("GENMASK"),
                "flags": self._regex_helper.group("FLAGS"),
                "mss": convert_to_number(self._regex_helper.group("MSS")),
                "window": convert_to_number(self._regex_helper.group("WINDOW")),
                "irtt": convert_to_number(self._regex_helper.group("IRTT")),
                "iface": self._regex_helper.group("INTERFACE"),
            }
            self.current_ret["ROUTING_TABLE"].append(_ret_dict)
            raise ParsingDone

    # IcmpMsg:
    _re_statistics = re.compile(r"^(?P<PROTO>\S+):$")

    def _parse_statistics(self, line):
        """
        Check if -s paramter is in use. If yes then parse corresponding values in line.
        Update those values to STATISTICS dictionary.

        :param line: Line to process.
        :return: None but raises ParsingDone if line has the information to handle by this method.
        """
        if "s" in self.options:
            if "STATISTICS" not in self.current_ret:
                self.current_ret["STATISTICS"] = {}
            if self._regex_helper.search_compiled(Netstat._re_statistics, line):
                self.statistics_proto = self._regex_helper.group("PROTO")
                self.current_ret["STATISTICS"][self.statistics_proto] = []
            else:
                self.current_ret["STATISTICS"][self.statistics_proto].append(
                    line.lstrip()
                )
            raise ParsingDone


COMMAND_OUTPUT = """
host:~ #   netstat
Active Internet connections (w/o servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State
tcp        0      0 localhost.localdo:20567 localhost.localdo:20570 ESTABLISHED
tcp        0      0 localhost.localdo:20567 localhost.localdo:20568 ESTABLISHED
sctp                localhost.localdo:65432                     LISTEN
sctp       1        localhost.localdo:65435                     LISTEN
sctp              1 localhost.localdo:65438   localhost.localdo:20537   LISTEN
Active UNIX domain sockets (w/o servers)
Proto RefCnt Flags       Type       State         I-Node   Path
unix  2      [ ]         DGRAM                    15365    /var/cache/samba/msg/846
unix  2      [ ]         DGRAM                    15404    /var/cache/samba/msg/878
host:~ # """

COMMAND_RESULT = {
    "UNIX_SOCKETS": [
        {
            "flags": "[ ]",
            "i-node": 15365,
            "path": "/var/cache/samba/msg/846",
            "proto": "unix",
            "refcnt": 2,
            "state": "",
            "type": "DGRAM",
        },
        {
            "flags": "[ ]",
            "i-node": 15404,
            "path": "/var/cache/samba/msg/878",
            "proto": "unix",
            "refcnt": 2,
            "state": "",
            "type": "DGRAM",
        },
    ],
    "INTERNET_CONNECTIONS": [
        {
            "foreign address": "localhost.localdo:20570",
            "local address": "localhost.localdo:20567",
            "proto": "tcp",
            "recv-q": 0,
            "send-q": 0,
            "state": "ESTABLISHED",
        },
        {
            "foreign address": "localhost.localdo:20568",
            "local address": "localhost.localdo:20567",
            "proto": "tcp",
            "recv-q": 0,
            "send-q": 0,
            "state": "ESTABLISHED",
        },
        {
            "foreign address": None,
            "local address": "localhost.localdo:65432",
            "proto": "sctp",
            "recv-q": None,
            "send-q": None,
            "state": "LISTEN",
        },
        {
            "foreign address": None,
            "local address": "localhost.localdo:65435",
            "proto": "sctp",
            "recv-q": 1,
            "send-q": None,
            "state": "LISTEN",
        },
        {
            "foreign address": "localhost.localdo:20537",
            "local address": "localhost.localdo:65438",
            "proto": "sctp",
            "recv-q": None,
            "send-q": 1,
            "state": "LISTEN",
        },
    ],
}

COMMAND_KWARGS = {}

COMMAND_OUTPUT_group = """
host:~ #   netstat -g
IPv6/IPv4 Group Memberships
Interface       RefCnt Group
--------------- ------ ---------------------
lo              1      all-systems.mcast.net
eth0            1      224.0.0.251
host:~ # """

COMMAND_RESULT_group = {
    "GROUP": [
        {"group": "all-systems.mcast.net", "interface": "lo", "refcnt": 1},
        {"group": "224.0.0.251", "interface": "eth0", "refcnt": 1},
    ]
}

COMMAND_KWARGS_group = {"options": "-g"}

COMMAND_OUTPUT_interface = """
host:~ #   netstat -i
Kernel Interface table
Iface   MTU Met   RX-OK RX-ERR RX-DRP RX-OVR    TX-OK TX-ERR TX-DRP TX-OVR Flg
eth0       1500 0    182746      0      0 0          1454      0      0      0 BMRU
lo        65536 0       687      0      0 0           687      0      0      0 LRU
host:~ # """

COMMAND_RESULT_interface = {
    "INTERFACE": [
        {
            "flg": "BMRU",
            "iface": "eth0",
            "met": 0,
            "mtu": 1500,
            "rx-drp": 0,
            "rx-err": 0,
            "rx-ok": 182746,
            "rx-ovr": 0,
            "tx-drp": 0,
            "tx-err": 0,
            "tx-ok": 1454,
            "tx-ovr": 0,
        },
        {
            "flg": "LRU",
            "iface": "lo",
            "met": 0,
            "mtu": 65536,
            "rx-drp": 0,
            "rx-err": 0,
            "rx-ok": 687,
            "rx-ovr": 0,
            "tx-drp": 0,
            "tx-err": 0,
            "tx-ok": 687,
            "tx-ovr": 0,
        },
    ]
}

COMMAND_KWARGS_interface = {"options": "-i"}

COMMAND_OUTPUT_routing_table = """
host:~ #   netstat -r
Kernel IP routing table
Destination     Gateway         Genmask         Flags   MSS Window  irtt Iface
default         123.123.123.123  0.0.0.0         UG        0 0          0 eth0
156.156.156.156    *               255.255.254.0   U         0 0          0 eth0
host:~ # """

COMMAND_RESULT_routing_table = {
    "ROUTING_TABLE": [
        {
            "destination": "default",
            "flags": "UG",
            "gateway": "123.123.123.123",
            "genmask": "0.0.0.0",
            "iface": "eth0",
            "irtt": 0,
            "mss": 0,
            "window": 0,
        },
        {
            "destination": "156.156.156.156",
            "flags": "U",
            "gateway": "*",
            "genmask": "255.255.254.0",
            "iface": "eth0",
            "irtt": 0,
            "mss": 0,
            "window": 0,
        },
    ]
}

COMMAND_KWARGS_routing_table = {"options": "-r"}

COMMAND_OUTPUT_pid = """
host:~ #   netstat -p
Active Internet connections (w/o servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name
tcp        0      0 localhost:45138         localhost:60002         ESTABLISHED 6919/egate
sctp                localhost.localdo:65432                     LISTEN      29004/sctp_1
sctp       1        localhost.localdo:65435                     LISTEN      29034/sctp_2
sctp              1 localhost.localdo:65438   localhost.localdo:20537   LISTEN      29045/sctp_3
Active UNIX domain sockets (w/o servers)
Active UNIX domain sockets (w/o servers)
Proto RefCnt Flags       Type       State         I-Node   PID/Program name    Path
unix  2      [ ]         DGRAM                    15390    -                   /var/cache/samba/msg/922
host:~ # """

COMMAND_RESULT_pid = {
    "INTERNET_CONNECTIONS": [
        {
            "foreign address": "localhost:60002",
            "local address": "localhost:45138",
            "pid/program name": "6919/egate",
            "proto": "tcp",
            "recv-q": 0,
            "send-q": 0,
            "state": "ESTABLISHED",
        },
        {
            "foreign address": None,
            "local address": "localhost.localdo:65432",
            "pid/program name": "29004/sctp_1",
            "proto": "sctp",
            "recv-q": None,
            "send-q": None,
            "state": "LISTEN",
        },
        {
            "foreign address": None,
            "local address": "localhost.localdo:65435",
            "pid/program name": "29034/sctp_2",
            "proto": "sctp",
            "recv-q": 1,
            "send-q": None,
            "state": "LISTEN",
        },
        {
            "foreign address": "localhost.localdo:20537",
            "local address": "localhost.localdo:65438",
            "pid/program name": "29045/sctp_3",
            "proto": "sctp",
            "recv-q": None,
            "send-q": 1,
            "state": "LISTEN",
        },
    ],
    "UNIX_SOCKETS": [
        {
            "flags": "[ ]",
            "i-node": 15390,
            "path": "/var/cache/samba/msg/922",
            "pid/program name": "-",
            "proto": "unix",
            "refcnt": 2,
            "state": "",
            "type": "DGRAM",
        }
    ],
}

COMMAND_KWARGS_pid = {"options": "-p"}

COMMAND_OUTPUT_statistics = """
host:~ #   netstat -s
IcmpMsg:
        InType3: 33
        InType8: 1
        OutType0: 1
        OutType3: 38
UdpLite:
Udp:
    117068 packets received
    38 packets to unknown port received.
    0 packet receive errors
    661 packets sent
host:~ # """

COMMAND_RESULT_statistics = {
    "STATISTICS": {
        "IcmpMsg": ["InType3: 33", "InType8: 1", "OutType0: 1", "OutType3: 38"],
        "Udp": [
            "117068 packets received",
            "38 packets to unknown port received.",
            "0 packet receive errors",
            "661 packets sent",
        ],
        "UdpLite": [],
    }
}

COMMAND_KWARGS_statistics = {"options": "-s"}
