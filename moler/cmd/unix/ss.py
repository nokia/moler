# -*- coding: utf-8 -*-
__author__ = 'Jakub Kupiec'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'jakub.kupiec@nokia.com'

import re
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone


class Ss(GenericUnixCommand):
    """Ss command class."""

    def __init__(self, connection, options="", prompt=None, newline_chars=None, runner=None):
        """
        Ss command.

        :param connection: Moler connection to device, terminal when command is executed.
        :param options: Options of ss command.
        :param prompt: Expected prompt that has been sent by device after command execution.
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        """
        super(Ss, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        # Parameters defined by calling the command
        self.options = options
        self._active = ''
        self.connection_index = 0
        self.current_ret = dict()
        self.current_ret['Network Connections'] = []

    def build_command_string(self):
        """
        Build command string from parameters passed to object.

        :return: String representation of the command to send over a connection to the device.
        """
        if self.options:
            cmd = "{} {}".format("ss", self.options)
        else:
            cmd = "{}".format("ss")
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Put your parsing code here.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: Nothing
        """
        try:
            if is_full_line:
                self._parse_headers(line)
                self._parse_sctp_streams(line)
        except ParsingDone:
            pass  # line has been fully parsed by one of above parse-methods
        return super(Ss, self).on_new_line(line, is_full_line)

    # Netid     State       Recv-Q Send-Q       Local Address:Port      Peer Address:Port
    _re_parse_groups = re.compile(r"^(?P<NETID>\w+)\s+(?P<STATE>\w+-\w+|\w+)\s+(?P<RECV_Q>\d+)\s+(?P<SEND_Q>\d+)\s+"
                                  r"(?P<LOCAL_ADDR>\S+)(?:\s|:){1}(?P<LOCAL_PORT>\w+)\s+(?P<PEER_ADDR>\S+)(?:\s|:){1}"
                                  r"(?P<PEER_PORT>\S+)")

    def _parse_headers(self, line):

        if self._regex_helper.search_compiled(Ss._re_parse_groups, line):
            socket_dict = dict()
            socket_dict['Netid'] = self._regex_helper.group("NETID")
            socket_dict['State'] = self._regex_helper.group("STATE")
            socket_dict['Recv-Q'] = self._regex_helper.group("RECV_Q")
            socket_dict['Send-Q'] = self._regex_helper.group("SEND_Q")
            socket_dict['Local Address'] = self._regex_helper.group("LOCAL_ADDR")
            socket_dict['Local Port'] = self._regex_helper.group("LOCAL_PORT")
            socket_dict['Peer Address'] = self._regex_helper.group("PEER_ADDR")
            socket_dict['Peer Port'] = self._regex_helper.group("PEER_PORT")
            self.current_ret['Network Connections'].append(socket_dict)
            self.connection_index = self.current_ret['Network Connections'].index(socket_dict)
            raise ParsingDone

    # State       Recv-Q Send-Q       Local Address     Local interface     :Port      Peer Address:Port
    _re_parse_sctp_stream = re.compile(r"^\s+`-\s(?P<STATE>\w+-\w+|\w+)\s+(?P<RECV_Q>\d+)\s+(?P<SEND_Q>\d+)\s+"
                                       r"(?P<LOCAL_ADDR>\S+)%(?P<INTERFACE>\w+)(?:\s|:){1}(?P<LOCAL_PORT>\w+)\s+"
                                       r"(?P<PEER_ADDR>\S+)(?:\s|:){1}(?P<PEER_PORT>\S+)")

    def _parse_sctp_streams(self, line):

        if self._regex_helper.search_compiled(Ss._re_parse_sctp_stream, line):
            self.current_ret['Network Connections'][self.connection_index]['Streams'] = []
            sctp_stream = dict()
            sctp_stream['State'] = self._regex_helper.group("STATE")
            sctp_stream['Recv-Q'] = self._regex_helper.group("RECV_Q")
            sctp_stream['Send-Q'] = self._regex_helper.group("SEND_Q")
            sctp_stream['Local Address'] = self._regex_helper.group("LOCAL_ADDR")
            sctp_stream['Local interface'] = self._regex_helper.group("INTERFACE")
            sctp_stream['Local Port'] = self._regex_helper.group("LOCAL_PORT")
            sctp_stream['Peer Address'] = self._regex_helper.group("PEER_ADDR")
            sctp_stream['Peer Port'] = self._regex_helper.group("PEER_PORT")
            self.current_ret['Network Connections'][self.connection_index]['Streams'].append(sctp_stream)
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

    'Network Connections': [{'Netid': 'u_str',
                             'State': 'SYN-SENT',
                             'Recv-Q': '0',
                             'Send-Q': '0',
                             'Local Address': '/var/run/rpcbind.sock',
                             'Local Port': '0',
                             'Peer Address': '*',
                             'Peer Port': '0'},
                            {'Netid': 'u_str',
                             'State': 'ESTAB',
                             'Recv-Q': '0',
                             'Send-Q': '0',
                             'Local Address': '/run/systemd/journal/stdout',
                             'Local Port': '13348',
                             'Peer Address': '*',
                             'Peer Port': '0'},
                            {'Netid': 'u_str',
                             'State': 'ESTAB',
                             'Recv-Q': '0',
                             'Send-Q': '0',
                             'Local Address': '*',
                             'Local Port': '19336',
                             'Peer Address': '*',
                             'Peer Port': '0'},
                            {'Netid': 'u_str',
                             'State': 'ESTAB',
                             'Recv-Q': '0',
                             'Send-Q': '0',
                             'Local Address': '/var/run/dbus/system_bus_socket',
                             'Local Port': '19386',
                             'Peer Address': '*',
                             'Peer Port': '0'},
                            {'Netid': 'udp',
                             'State': 'ESTAB',
                             'Recv-Q': '0',
                             'Send-Q': '0',
                             'Local Address': '192.168.253.237',
                             'Local Port': '55635',
                             'Peer Address': '192.168.253.237',
                             'Peer Port': '20400'},
                            {'Netid': 'udp',
                             'State': 'ESTAB',
                             'Recv-Q': '0',
                             'Send-Q': '0',
                             'Local Address': '192.168.253.237',
                             'Local Port': '40537',
                             'Peer Address': '192.168.253.237',
                             'Peer Port': '20400'},
                            {'Netid': 'tcp',
                             'State': 'ESTAB',
                             'Recv-Q': '0',
                             'Send-Q': '0',
                             'Local Address': '127.0.0.1',
                             'Local Port': 'gpsd',
                             'Peer Address': '127.0.0.1',
                             'Peer Port': '40488'},
                            {'Netid': 'tcp',
                             'State': 'ESTAB',
                             'Recv-Q': '0',
                             'Send-Q': '0',
                             'Local Address': '::ffff:127.0.0.1',
                             'Local Port': '60758',
                             'Peer Address': '::ffff:127.0.0.1',
                             'Peer Port': '20483'},
                            {'Netid': 'tcp',
                             'State': 'ESTAB',
                             'Recv-Q': '0',
                             'Send-Q': '0',
                             'Local Address': '::ffff:192.168.253.16',
                             'Local Port': '54930',
                             'Peer Address': '::ffff:192.168.253.231',
                             'Peer Port': '30500'},
                            {'Netid': 'sctp',
                             'State': 'ESTAB',
                             'Recv-Q': '0',
                             'Send-Q': '0',
                             'Local Address': '192.168.253.16',
                             'Local Port': '29211',
                             'Peer Address': '*',
                             'Peer Port': '29211',
                             'Streams': [{'State': 'ESTAB',
                                          'Recv-Q': '0',
                                          'Send-Q': '0',
                                          'Local Address': '192.168.253.16',
                                          'Local interface': 'etha01',
                                          'Local Port': '29211',
                                          'Peer Address': '192.168.253.17',
                                          'Peer Port': '29211'}]
                             },
                            {'Netid': 'sctp',
                             'State': 'LISTEN',
                             'Recv-Q': '0',
                             'Send-Q': '128',
                             'Local Address': '192.168.253.16',
                             'Local Port': '38462',
                             'Peer Address': '*',
                             'Peer Port': '*',
                             'Streams': [{'State': 'ESTAB',
                                          'Recv-Q': '0',
                                          'Send-Q': '0',
                                          'Local Address': '192.168.253.1',
                                          'Local interface': 'etha01',
                                          'Local Port': '38462',
                                          'Peer Address': '192.168.253.17',
                                          'Peer Port': '38462'}]
                             },
                            {'Netid': 'sctp',
                             'State': 'LISTEN',
                             'Recv-Q': '0',
                             'Send-Q': '128',
                             'Local Address': '10.83.183.63',
                             'Local Port': '32742',
                             'Peer Address': '*',
                             'Peer Port': '*',
                             'Streams': [{'State': 'ESTAB',
                                          'Recv-Q': '0',
                                          'Send-Q': '0',
                                          'Local Address': '10.83.183.63',
                                          'Local interface': 'fp0',
                                          'Local Port': '32742',
                                          'Peer Address': '10.83.183.67',
                                          'Peer Port': '32742'}]
                             }]}

COMMAND_KWARGS = {}
