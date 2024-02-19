# -*- coding: utf-8 -*-
__author__ = "Jakub Kupiec, Marcin Usielski"
__copyright__ = "Copyright (C) 2020, Nokia"
__email__ = "jakub.kupiec@nokia.com, marcin.usielski@nokia.com"

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone
from moler.helpers import convert_to_number


class Ss(GenericUnixCommand):
    """Ss command class."""

    def __init__(
        self, connection, options="", prompt=None, newline_chars=None, runner=None
    ):
        """
        Ss command.

        :param connection: Moler connection to device, terminal when command is executed.
        :param options: Options of ss command.
        :param prompt: Expected prompt that has been sent by device after command execution.
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        """
        super(Ss, self).__init__(
            connection=connection,
            prompt=prompt,
            newline_chars=newline_chars,
            runner=runner,
        )
        # Parameters defined by calling the command
        self.options = options
        self.connection_index = 0
        self.current_ret["NETWORK_CONNECTIONS"] = []

    def build_command_string(self):
        """
        Build command string from parameters passed to object.

        :return: String representation of the command to send over a connection to the device.
        """
        if self.options:
            cmd = f"ss {self.options}"
        else:
            cmd = "ss"
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
                self._parse_headers(line)
                self._parse_sctp_streams(line)
        except ParsingDone:
            pass  # line has been fully parsed by one of above parse-methods
        return super(Ss, self).on_new_line(line, is_full_line)

    # Netid     State       Recv-Q Send-Q       Local Address:Port      Peer Address:Port
    _re_parse_groups = re.compile(
        r"^((?P<NETID>\w+)\s+)?(?P<STATE>\w+-\w+|\w+)\s+(?P<RECV_Q>\d+)\s+(?P<SEND_Q>\d+)\s+"
        r"(?P<LOCAL_ADDR>\S+)(?:\s|:){1}(?P<LOCAL_PORT>\w+)\s+(?P<PEER_ADDR>\S+)(?:\s|:){1}"
        r"(?P<PEER_PORT>\S+)"
    )

    def _parse_headers(self, line):
        if self._regex_helper.search_compiled(Ss._re_parse_groups, line):
            socket_dict = {}
            socket_dict["netid"] = self._regex_helper.group("NETID")
            socket_dict["state"] = self._regex_helper.group("STATE")
            socket_dict["recv-Q"] = convert_to_number(
                self._regex_helper.group("RECV_Q")
            )
            socket_dict["send-Q"] = convert_to_number(
                self._regex_helper.group("SEND_Q")
            )
            socket_dict["local_address"] = self._regex_helper.group("LOCAL_ADDR")
            socket_dict["local_port"] = self._regex_helper.group("LOCAL_PORT")
            socket_dict["peer_address"] = self._regex_helper.group("PEER_ADDR")
            socket_dict["peer_port"] = self._regex_helper.group("PEER_PORT")
            self.current_ret["NETWORK_CONNECTIONS"].append(socket_dict)
            self.connection_index = self.current_ret["NETWORK_CONNECTIONS"].index(
                socket_dict
            )
            raise ParsingDone

    # State       Recv-Q Send-Q       Local Address     Local interface     :Port      Peer Address:Port
    _re_parse_sctp_stream = re.compile(
        r"^\s+`-\s(?P<STATE>\w+-\w+|\w+)\s+(?P<RECV_Q>\d+)\s+(?P<SEND_Q>\d+)\s+"
        r"(?P<LOCAL_ADDR>\S+)%(?P<INTERFACE>\w+)(?:\s|:){1}(?P<LOCAL_PORT>\w+)\s+"
        r"(?P<PEER_ADDR>\S+)(?:\s|:){1}(?P<PEER_PORT>\S+)"
    )

    def _parse_sctp_streams(self, line):
        if self._regex_helper.search_compiled(Ss._re_parse_sctp_stream, line):
            self.current_ret["NETWORK_CONNECTIONS"][self.connection_index][
                "streams"
            ] = []
            sctp_stream = {}
            sctp_stream["state"] = self._regex_helper.group("STATE")
            sctp_stream["recv-Q"] = convert_to_number(
                self._regex_helper.group("RECV_Q")
            )
            sctp_stream["send-Q"] = convert_to_number(
                self._regex_helper.group("SEND_Q")
            )
            sctp_stream["local_address"] = self._regex_helper.group("LOCAL_ADDR")
            sctp_stream["local_interface"] = self._regex_helper.group("INTERFACE")
            sctp_stream["local_port"] = self._regex_helper.group("LOCAL_PORT")
            sctp_stream["peer_address"] = self._regex_helper.group("PEER_ADDR")
            sctp_stream["peer_port"] = self._regex_helper.group("PEER_PORT")
            self.current_ret["NETWORK_CONNECTIONS"][self.connection_index][
                "streams"
            ].append(sctp_stream)
            raise ParsingDone


COMMAND_OUTPUT = """
root@fct-0a:~ >ss
Netid State      Recv-Q Send-Q                          Local Address:Port                                           Peer Address:Port
u_str SYN-SENT   0      0                       /var/run/rpcbind.sock 0                                                         * 0
u_str ESTAB      0      0                 /run/systemd/journal/stdout 13348                                                     * 0
u_str ESTAB      0      0                                           * 19336                                                     * 0
u_str ESTAB      0      0             /var/run/dbus/system_bus_socket 19386                                                     * 0
udp   ESTAB      0      0                             192.168.253.237:55635                                       192.168.253.237:20400
udp   ESTAB      0      0                             192.168.253.237:40537                                       192.168.253.237:20400
tcp   ESTAB      0      0                                   127.0.0.1:gpsd                                              127.0.0.1:40488
tcp   ESTAB      0      0                            ::ffff:127.0.0.1:60758                                      ::ffff:127.0.0.1:20483
tcp   ESTAB      0      0                       ::ffff:192.168.253.16:54930                                ::ffff:192.168.253.231:30500
sctp  ESTAB      0      0                              192.168.253.16:29211                                                     *:29211
      `- ESTAB   0      0                       192.168.253.16%etha01:29211                                        192.168.253.17:29211
sctp  LISTEN     0      128                            192.168.253.16:38462                                                     *:*
      `- ESTAB   0      0                        192.168.253.1%etha01:38462                                        192.168.253.17:38462
sctp  LISTEN     0      128                              10.83.183.63:32742                                                     *:*
      `- ESTAB   0      0                            10.83.183.63%fp0:32742                                          10.83.183.67:32742
root@fct-0a:~ >
"""

COMMAND_RESULT = {
    "NETWORK_CONNECTIONS": [
        {
            "netid": "u_str",
            "state": "SYN-SENT",
            "recv-Q": 0,
            "send-Q": 0,
            "local_address": "/var/run/rpcbind.sock",
            "local_port": "0",
            "peer_address": "*",
            "peer_port": "0",
        },
        {
            "netid": "u_str",
            "state": "ESTAB",
            "recv-Q": 0,
            "send-Q": 0,
            "local_address": "/run/systemd/journal/stdout",
            "local_port": "13348",
            "peer_address": "*",
            "peer_port": "0",
        },
        {
            "netid": "u_str",
            "state": "ESTAB",
            "recv-Q": 0,
            "send-Q": 0,
            "local_address": "*",
            "local_port": "19336",
            "peer_address": "*",
            "peer_port": "0",
        },
        {
            "netid": "u_str",
            "state": "ESTAB",
            "recv-Q": 0,
            "send-Q": 0,
            "local_address": "/var/run/dbus/system_bus_socket",
            "local_port": "19386",
            "peer_address": "*",
            "peer_port": "0",
        },
        {
            "netid": "udp",
            "state": "ESTAB",
            "recv-Q": 0,
            "send-Q": 0,
            "local_address": "192.168.253.237",
            "local_port": "55635",
            "peer_address": "192.168.253.237",
            "peer_port": "20400",
        },
        {
            "netid": "udp",
            "state": "ESTAB",
            "recv-Q": 0,
            "send-Q": 0,
            "local_address": "192.168.253.237",
            "local_port": "40537",
            "peer_address": "192.168.253.237",
            "peer_port": "20400",
        },
        {
            "netid": "tcp",
            "state": "ESTAB",
            "recv-Q": 0,
            "send-Q": 0,
            "local_address": "127.0.0.1",
            "local_port": "gpsd",
            "peer_address": "127.0.0.1",
            "peer_port": "40488",
        },
        {
            "netid": "tcp",
            "state": "ESTAB",
            "recv-Q": 0,
            "send-Q": 0,
            "local_address": "::ffff:127.0.0.1",
            "local_port": "60758",
            "peer_address": "::ffff:127.0.0.1",
            "peer_port": "20483",
        },
        {
            "netid": "tcp",
            "state": "ESTAB",
            "recv-Q": 0,
            "send-Q": 0,
            "local_address": "::ffff:192.168.253.16",
            "local_port": "54930",
            "peer_address": "::ffff:192.168.253.231",
            "peer_port": "30500",
        },
        {
            "netid": "sctp",
            "state": "ESTAB",
            "recv-Q": 0,
            "send-Q": 0,
            "local_address": "192.168.253.16",
            "local_port": "29211",
            "peer_address": "*",
            "peer_port": "29211",
            "streams": [
                {
                    "state": "ESTAB",
                    "recv-Q": 0,
                    "send-Q": 0,
                    "local_address": "192.168.253.16",
                    "local_interface": "etha01",
                    "local_port": "29211",
                    "peer_address": "192.168.253.17",
                    "peer_port": "29211",
                }
            ],
        },
        {
            "netid": "sctp",
            "state": "LISTEN",
            "recv-Q": 0,
            "send-Q": 128,
            "local_address": "192.168.253.16",
            "local_port": "38462",
            "peer_address": "*",
            "peer_port": "*",
            "streams": [
                {
                    "state": "ESTAB",
                    "recv-Q": 0,
                    "send-Q": 0,
                    "local_address": "192.168.253.1",
                    "local_interface": "etha01",
                    "local_port": "38462",
                    "peer_address": "192.168.253.17",
                    "peer_port": "38462",
                }
            ],
        },
        {
            "netid": "sctp",
            "state": "LISTEN",
            "recv-Q": 0,
            "send-Q": 128,
            "local_address": "10.83.183.63",
            "local_port": "32742",
            "peer_address": "*",
            "peer_port": "*",
            "streams": [
                {
                    "state": "ESTAB",
                    "recv-Q": 0,
                    "send-Q": 0,
                    "local_address": "10.83.183.63",
                    "local_interface": "fp0",
                    "local_port": "32742",
                    "peer_address": "10.83.183.67",
                    "peer_port": "32742",
                }
            ],
        },
    ]
}

COMMAND_KWARGS = {}

COMMAND_OUTPUT_t = """ss -t
State      Recv-Q Send-Q    Local Address:Port        Peer Address:Port
ESTAB      0      0           192.168.1.2:43839     108.160.162.37:http
ESTAB      0      0           192.168.1.2:43622     199.59.149.201:https
client@server$"""

COMMAND_KWARGS_t = {"options": "-t"}

COMMAND_RESULT_t = {
    "NETWORK_CONNECTIONS": [
        {
            "local_address": "192.168.1.2",
            "local_port": "43839",
            "netid": None,
            "peer_address": "108.160.162.37",
            "peer_port": "http",
            "recv-Q": 0,
            "send-Q": 0,
            "state": "ESTAB",
        },
        {
            "local_address": "192.168.1.2",
            "local_port": "43622",
            "netid": None,
            "peer_address": "199.59.149.201",
            "peer_port": "https",
            "recv-Q": 0,
            "send-Q": 0,
            "state": "ESTAB",
        },
    ]
}
