# -*- coding: utf-8 -*-
"""
Mpstat command module.
"""

__author__ = 'Julia Patacz'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'julia.patacz@nokia.com'

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone


class Ping(GenericUnixCommand):

    def __init__(self, connection, destination, options=None, prompt=None, newline_chars=None, runner=None):
        super(Ping, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        # Parameters defined by calling the command
        self.options = options
        self.destination = destination

    def build_command_string(self):
        if ":" in self.destination:
            cmd = "ping6 {}".format(self.destination)
        else:
            cmd = "ping {}".format(self.destination)
        if self.options:
            cmd = "{} {}".format(cmd, self.options)
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_trans_recv_loss_time(line)
                self._parse_min_avg_max_mdev_unit_time(line)
            except ParsingDone:
                pass  # line has been fully parsed by one of above parse-methods
        return super(Ping, self).on_new_line(line, is_full_line)

    # 11 packets transmitted, 11 received, 0 % packet loss, time 9999 ms
    _re_trans_recv_loss_time = re.compile(
        r"(?P<PKTS_TRANS>\d+) packets transmitted, (?P<PKTS_RECV>\d+) received, (?P<PKT_LOSS>\S+)% packet loss, time (?P<TIME>\S+)")

    def _parse_trans_recv_loss_time(self, line):
        if self._regex_helper.search_compiled(Ping._re_trans_recv_loss_time, line):
            self.current_ret['packets_transmitted'] = self._regex_helper.group('PKTS_TRANS')
            self.current_ret['packets_received'] = self._regex_helper.group('PKTS_RECV')
            self.current_ret['packet_loss'] = self._regex_helper.group('PKT_LOSS')
            self.current_ret['time'] = self._regex_helper.group('TIME')
            raise ParsingDone

    # rtt min/avg/max/mdev = 0.033/0.050/0.084/0.015 ms
    _re_min_avg_max_mdev_unit_time = re.compile(
        r"rtt min\/avg\/max\/mdev = (?P<MIN>\S+)\/(?P<AVG>\S+)\/(?P<MAX>\S+)\/(?P<MDEV>\S+)\s+(?P<UNIT>\S+)")

    def _parse_min_avg_max_mdev_unit_time(self, line):
        if self._regex_helper.search_compiled(Ping._re_min_avg_max_mdev_unit_time, line):
            self.current_ret['time_min'] = self._regex_helper.group('MIN')
            self.current_ret['time_avg'] = self._regex_helper.group('AVG')
            self.current_ret['time_max'] = self._regex_helper.group('MAX')
            self.current_ret['time_mdev'] = self._regex_helper.group('MDEV')
            self.current_ret['time_unit'] = self._regex_helper.group('UNIT')
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
    'packets_transmitted': '6',
    'packets_received': '6',
    'packet_loss': '0',
    'time': '4996ms',
    'time_min': '0.035',
    'time_avg': '0.045',
    'time_max': '0.062',
    'time_mdev': '0.012',
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
    'packets_transmitted': '6',
    'packets_received': '6',
    'packet_loss': '0',
    'time': '4999ms',
    'time_min': '0.022',
    'time_avg': '0.049',
    'time_max': '0.070',
    'time_mdev': '0.019',
    'time_unit': 'ms',
}
