# -*- coding: utf-8 -*-
"""
Ping command module.
"""

__author__ = 'Julia Patacz, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'julia.patacz@nokia.com, marcin.usielski@nokia.com'

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone
from moler.util.converterhelper import ConverterHelper


class Ping(GenericUnixCommand):

    def __init__(self, connection, destination, options=None, prompt=None, newline_chars=None, runner=None):
        """
        Ping command.
        :param connection: moler connection to device, terminal when command is executed.
        :param destination: address (IP v4 or v6) of unit to ping.
        :param options: options of ping command for unix.
        :param prompt: prompt on system where ping is executed.
        :param newline_chars: characters to split lines.
        :param runner: Runner to run command
        """
        super(Ping, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        # Parameters defined by calling the command
        self.options = options
        self.destination = destination
        self._converter_helper = ConverterHelper.get_converter_helper()

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.
        :return: String representation of command to send over connection to device.
        """
        if ":" in self.destination:
            cmd = "ping6 {}".format(self.destination)
        else:
            cmd = "ping {}".format(self.destination)
        if self.options:
            cmd = "{} {}".format(cmd, self.options)
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Put your parsing code here.
        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: Nothing
        """
        if is_full_line:
            try:
                self._parse_trans_recv_loss_time_plus_errors(line)
                self._parse_trans_recv_loss_time(line)
                self._parse_min_avg_max_mdev_unit_time(line)
            except ParsingDone:
                pass  # line has been fully parsed by one of above parse-methods
        return super(Ping, self).on_new_line(line, is_full_line)

    # 11 packets transmitted, 11 received, 0 % packet loss, time 9999 ms
    _re_trans_recv_loss_time = re.compile(
        r"(?P<PKTS_TRANS>\d+) packets transmitted, (?P<PKTS_RECV>\d+) received, (?P<PKT_LOSS>\S+)% packet loss, time (?P<TIME>\d+)\s*(?P<UNIT>\w+)")

    def _parse_trans_recv_loss_time(self, line):
        """
        Parses packets from the line of command output
        :param line: Line of output of command.
        :return: Nothing but raises ParsingDone if line has information to handle by this method.
        """
        if self._regex_helper.search_compiled(Ping._re_trans_recv_loss_time, line):
            self.current_ret['packets_transmitted'] = int(self._regex_helper.group('PKTS_TRANS'))
            self.current_ret['packets_received'] = int(self._regex_helper.group('PKTS_RECV'))
            self.current_ret['packet_loss'] = int(self._regex_helper.group('PKT_LOSS'))
            self.current_ret['time'] = int(self._regex_helper.group('TIME'))
            self.current_ret['packets_time_unit'] = self._regex_helper.group('UNIT')
            value_in_seconds = self._converter_helper.to_seconds(self.current_ret['time'], self.current_ret['packets_time_unit'])
            self.current_ret['time_seconds'] = value_in_seconds
            raise ParsingDone

    # 4 packets transmitted, 3 received, +1 errors, 25% packet loss, time 3008ms
    _re_trans_recv_loss_time_plus_errors = re.compile(
        r"(?P<PKTS_TRANS>\d+) packets transmitted, (?P<PKTS_RECV>\d+) received, \+?(?P<ERRORS>\d+) errors, (?P<PKT_LOSS>\S+)% packet loss, time (?P<TIME>\d+)\s*(?P<UNIT>\w+)")

    def _parse_trans_recv_loss_time_plus_errors(self, line):
        """
        Parses packets from the line of command output
        :param line: Line of output of command.
        :return: Nothing but raises ParsingDone if line has information to handle by this method.
        """
        if self._regex_helper.search_compiled(Ping._re_trans_recv_loss_time_plus_errors, line):
            self.current_ret['packets_transmitted'] = int(self._regex_helper.group('PKTS_TRANS'))
            self.current_ret['packets_received'] = int(self._regex_helper.group('PKTS_RECV'))
            self.current_ret['errors'] = int(self._regex_helper.group('ERRORS'))
            self.current_ret['packet_loss'] = int(self._regex_helper.group('PKT_LOSS'))
            self.current_ret['time'] = int(self._regex_helper.group('TIME'))
            self.current_ret['packets_time_unit'] = self._regex_helper.group('UNIT')
            value_in_seconds = self._converter_helper.to_seconds(self.current_ret['time'],
                                                                 self.current_ret['packets_time_unit'])
            self.current_ret['time_seconds'] = value_in_seconds
            raise ParsingDone

    # rtt min/avg/max/mdev = 0.033/0.050/0.084/0.015 ms
    _re_min_avg_max_mdev_unit_time = re.compile(
        r"rtt min\/avg\/max\/mdev = (?P<MIN>[\d\.]+)\/(?P<AVG>[\d\.]+)\/(?P<MAX>[\d\.]+)\/(?P<MDEV>[\d\.]+)\s+(?P<UNIT>\w+)")

    def _parse_min_avg_max_mdev_unit_time(self, line):
        """
        Parses rrt info form the line of command output
        :param line: Line of output of command
        :return: Nothing but raises ParsingDone if line has information to handle by this method.
        """
        if self._regex_helper.search_compiled(Ping._re_min_avg_max_mdev_unit_time, line):
            unit = self._regex_helper.group('UNIT')
            time_min = float(self._regex_helper.group('MIN'))
            time_min_sec = self._converter_helper.to_seconds(time_min, unit)
            time_avg = float(self._regex_helper.group('AVG'))
            time_avg_sec = self._converter_helper.to_seconds(time_avg, unit)
            time_max = float(self._regex_helper.group('MAX'))
            time_max_sec = self._converter_helper.to_seconds(time_max, unit)
            time_mdev = float(self._regex_helper.group('MDEV'))
            time_mdev_sec = self._converter_helper.to_seconds(time_mdev, unit)
            self.current_ret['time_unit'] = unit
            self.current_ret['time_min'] = time_min
            self.current_ret['time_min_seconds'] = time_min_sec
            self.current_ret['time_avg'] = time_avg
            self.current_ret['time_avg_seconds'] = time_avg_sec
            self.current_ret['time_max'] = time_max
            self.current_ret['time_max_seconds'] = time_max_sec
            self.current_ret['time_mdev'] = time_mdev
            self.current_ret['time_mdev_seconds'] = time_mdev_sec

            raise ParsingDone


COMMAND_OUTPUT = """
ute@debdev:~/moler_int$ ping localhost -w 5
PING localhost (127.0.0.1) 56(84) bytes of data.
64 bytes from localhost (127.0.0.1): icmp_seq=1 ttl=64 time=0.047 ms
64 bytes from localhost (127.0.0.1): icmp_seq=2 ttl=64 time=0.039 ms
64 bytes from localhost (127.0.0.1): icmp_seq=3 ttl=64 time=0.041 ms
64 bytes from localhost (127.0.0.1): icmp_seq=4 ttl=64 time=0.035 ms
64 bytes from localhost (127.0.0.1): icmp_seq=5 ttl=64 time=0.051 ms
64 bytes from localhost (127.0.0.1): icmp_seq=6 ttl=64 time=0.062 ms

--- localhost ping statistics ---
6 packets transmitted, 6 received, 0% packet loss, time 4996ms
rtt min/avg/max/mdev = 0.035/0.045/0.062/0.012 ms
ute@debdev:~/moler_int$ """
COMMAND_KWARGS = {'destination': 'localhost',
                  'options': '-w 5'}
COMMAND_RESULT = {
    'packets_transmitted': 6,
    'packets_received': 6,
    'packet_loss': 0,
    'time': 4996,
    'time_seconds': 4.996,
    'packets_time_unit': 'ms',
    'time_min': 0.035,
    'time_avg': 0.045,
    'time_max': 0.062,
    'time_mdev': 0.012,
    'time_min_seconds': 0.035 * 0.001,
    'time_avg_seconds': 0.045 * 0.001,
    'time_max_seconds': 0.062 * 0.001,
    'time_mdev_seconds': 0.012 * 0.001,
    'time_unit': 'ms',
}

COMMAND_OUTPUT_v6 = """ute@debdev:~/moler_int$ ping6 ::1 -w 5
PING ::1(::1) 56 data bytes
64 bytes from ::1: icmp_seq=1 ttl=64 time=0.028 ms
64 bytes from ::1: icmp_seq=2 ttl=64 time=0.042 ms
64 bytes from ::1: icmp_seq=3 ttl=64 time=0.022 ms
64 bytes from ::1: icmp_seq=4 ttl=64 time=0.067 ms
64 bytes from ::1: icmp_seq=5 ttl=64 time=0.066 ms
64 bytes from ::1: icmp_seq=6 ttl=64 time=0.070 ms

--- ::1 ping statistics ---
6 packets transmitted, 6 received, 0% packet loss, time 4999ms
rtt min/avg/max/mdev = 0.022/0.049/0.070/0.019 ms
ute@debdev:~/moler_int$"""

COMMAND_KWARGS_v6 = {
    'destination': '::1',
    'options': '-w 5'
}

COMMAND_RESULT_v6 = {
    'packets_transmitted': 6,
    'packets_received': 6,
    'packet_loss': 0,
    'time': 4999,
    'time_seconds': 4.999,
    'packets_time_unit': 'ms',
    'time_min': 0.022,
    'time_avg': 0.049,
    'time_max': 0.070,
    'time_mdev': 0.019,
    'time_min_seconds': 0.022 * 0.001,
    'time_avg_seconds': 0.049 * 0.001,
    'time_max_seconds': 0.070 * 0.001,
    'time_mdev_seconds': 0.019 * 0.001,
    'time_unit': 'ms',
}


COMMAND_OUTPUT_pipe = """ping 192.168.1.1 -c 4
PING 192.168.1.1 (192.168.1.1) 56(84) bytes of data.
From 192.168.1.1 icmp_seq=1 Destination Host Unreachable
64 bytes from 192.168.1.1: icmp_seq=2 ttl=64 time=1260 ms
64 bytes from 192.168.1.1: icmp_seq=3 ttl=64 time=253 ms
64 bytes from 192.168.1.1: icmp_seq=4 ttl=64 time=0.408 ms

--- 192.168.255.129 ping statistics ---
4 packets transmitted, 3 received, +1 errors, 25% packet loss, time 3008ms
rtt min/avg/max/mdev = 0.408/504.817/1260.131/544.022 ms, pipe 2
moler@moler:>"""

COMMAND_KWARGS_pipe = {
    'destination': '192.168.1.1',
    'options': '-c 4'
}

COMMAND_RESULT_pipe = {
    'packets_transmitted': 4,
    'packets_received': 3,
    'packet_loss': 25,
    'time': 3008,
    'time_seconds': 3.008,
    'packets_time_unit': 'ms',
    'errors': 1,
    'time_min': 0.408,
    'time_avg': 504.817,
    'time_max': 1260.131,
    'time_mdev': 544.022,
    'time_min_seconds': 0.408 * 0.001,
    'time_avg_seconds': 504.817 * 0.001,
    'time_max_seconds': 1260.131 * 0.001,
    'time_mdev_seconds': 544.022 * 0.001,
    'time_unit': 'ms',
}
