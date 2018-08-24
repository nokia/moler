# -*- coding: utf-8 -*-
"""
Tcpdump command module.
"""

__author__ = 'Julia Patacz'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'julia.patacz@nokia.com'

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone


class Tcpdump(GenericUnixCommand):

    def __init__(self, connection, options=None, prompt=None, new_line_chars=None):
        super(Tcpdump, self).__init__(connection, prompt, new_line_chars)
        # Parameters defined by calling the command
        self.options = options

        self.ret_required = False

    def build_command_string(self):
        cmd = "tcpdump"
        if self.options:
            cmd = "{} {}".format(cmd, self.options)
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self.parse_packets(line)
            except ParsingDone:
                pass
        return super(Tcpdump, self).on_new_line(line, is_full_line)

    # 5 packets received by filter
    _re_packets_captured = re.compile(
        r"(?P<PCKT>\d+)\s+(?P<GROUP>packets captured|packets received by filter|packets dropped by kernel)")

    def parse_packets(self, line):
        if self._regex_helper.search_compiled(Tcpdump._re_packets_captured, line):
            temp_pckt = self._regex_helper.group('PCKT')
            temp_group = self._regex_helper.group('GROUP')
            self.current_ret[temp_group] = temp_pckt


COMMAND_OUTPUT = """
ute@debdev:~$ tcpdump -c 4
tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
listening on eth0, link-type EN10MB (Ethernet), capture size 262144 bytes
13:16:22.176856 IP debdev.ntp > fwdns2.vbctv.in.ntp: NTPv4, Client, length 48
13:16:22.178451 IP debdev.44321 > rumcdc001.nsn-intra.net.domain: 34347+ PTR? 124.200.108.123.in-addr.arpa. (46)
13:16:22.178531 IP debdev.44321 > fihedc002.emea.nsn-net.net.domain: 34347+ PTR? 124.200.108.123.in-addr.arpa. (46)
13:16:22.178545 IP debdev.44321 > fihedc001.emea.nsn-net.net.domain: 34347+ PTR? 124.200.108.123.in-addr.arpa. (46)
4 packets captured
5 packets received by filter
0 packets dropped by kernel
ute@debdev:~$ """
COMMAND_KWARGS = {
    'options': '-c 4',
}
COMMAND_RESULT = {
    'packets captured': '4',
    'packets received by filter': '5',
    'packets dropped by kernel': '0',
}

COMMAND_OUTPUT_vv = """ute@debdev:~$ sudo tcpdump -c 4 -vv
tcpdump: listening on eth0, link-type EN10MB (Ethernet), capture size 262144 bytes
13:31:33.176710 IP (tos 0xc0, ttl 64, id 4236, offset 0, flags [DF], proto UDP (17), length 76)
    debdev.ntp > ntp.wdc1.us.leaseweb.net.ntp: [bad udp cksum 0x7aab -> 0x9cd3!] NTPv4, length 48
    Client, Leap indicator: clock unsynchronized (192), Stratum 0 (unspecified), poll 10 (1024s), precision -23
    Root Delay: 0.000000, Root dispersion: 1.031906, Reference-ID: (unspec)
      Reference Timestamp:  0.000000000
      Originator Timestamp: 0.000000000
      Receive Timestamp:    0.000000000
      Transmit Timestamp:   3741593493.176683590 (2018/07/26 13:31:33)
        Originator - Receive Timestamp:  0.000000000
        Originator - Transmit Timestamp: 3741593493.176683590 (2018/07/26 13:31:33)
13d:31:36.177597 IP (tos 0xc0, ttl 64, id 37309, offset 0, flags [DF], proto UDP (17), length 76)
    debdev.ntp > dream.multitronic.fi.ntp: [ba udp cksum 0x6b9b -> 0x0677!] NTPv4, length 48
    Client, Leap indicator: clock unsynchronized (192), Stratum 0 (unspecified), poll 10 (1024s), precision -23
    Root Delay: 0.000000, Root dispersion: 1.031951, Reference-ID: (unspec)
      Reference Timestamp:  0.000000000
      Originator Timestamp: 0.000000000
      Receive Timestamp:    0.000000000
      Transmit Timestamp:   3741593496.177547928 (2018/07/26 13:31:36)
        Originator - Receive Timestamp:  0.000000000
        Originator - Transmit Timestamp: 3741593496.177547928 (2018/07/26 13:31:36)
13:31:36.178110 IP (tos 0x0, ttl 64, id 3207, offset 0, flags [DF], proto UDP (17), length 72)
    debdev.6869 > rumcdc001.nsn-intra.net.domain: [bad udp cksum 0x96f8 -> 0x405b!] 61207+ PTR? 38.138.28.213.in-addr.arpa. (44)
13:31:36.178211 IP (tos 0x0, ttl 64, id 63672, offset 0, flags [DF], proto UDP (17), length 72)
    debdev.6869 > fihedc002.emea.nsn-net.net.domain: [bad udp cksum 0x49fe -> 0x8d55!] 61207+ PTR? 38.138.28.213.in-addr.arpa. (44)
4 packets captured
6 packets received by filter
0 packets dropped by kernel
ute@debdev:~$ """
COMMAND_KWARGS_vv = {
    'options': '-c 4 -vv'
}
COMMAND_RESULT_vv = {
    'packets captured': '4',
    'packets received by filter': '6',
    'packets dropped by kernel': '0',
}
