# -*- coding: utf-8 -*-
"""
Tshark command module.
"""

__author__ = 'Julia Patacz'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'julia.patacz@nokia.com'

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone


class Tshark(GenericUnixCommand):

    def __init__(self, connection, options=None, prompt=None, newline_chars=None, runner=None):
        super(Tshark, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        # Parameters defined by calling the command
        self.options = options
        self.pckt_count = None
        self.current_ret = {}
        self.ret_required = False

    def build_command_string(self):
        cmd = 'tshark'
        if self.options:
            cmd = f'{cmd} {self.options}'
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_pckt_time_src_dst_proto_id_seq_ttl(line)
                self._parse_pckt_time_src_dst_proto_id_seq_hop_limit(line)
                self._parse_pckts_captured(line)
            except ParsingDone:
                pass  # line has been fully parsed by one of above parse-methods
        return super(Tshark, self).on_new_line(line, is_full_line)

    # 1 0.000000000    127.0.0.1 → 127.0.0.1    ICMP 98 Echo (ping) request  id=0x693b, seq=48/12288, ttl=64
    _re_pckt_time_src_dst_proto_id_seq_ttl = re.compile(
        r"\s+(?P<PCKT>\d+)\s+(?P<TIME>\S+)\s+(?P<SRC>\S+)\s+[^A-Za-z0-9\s]\s+(?P<DST>\S+)\s+(?P<PROTO>.*)\s+id=(?P<ID>\S+),\s+seq=(?P<SEQ>\S+),\s+ttl=(?P<TTL>\S+).*$")

    def _parse_pckt_time_src_dst_proto_id_seq_ttl(self, line):
        if self._regex_helper.search_compiled(Tshark._re_pckt_time_src_dst_proto_id_seq_ttl, line):
            temp_pckt = self._regex_helper.group('PCKT')
            self.current_ret[temp_pckt] = {}
            self.current_ret[temp_pckt]['time'] = self._regex_helper.group('TIME')
            self.current_ret[temp_pckt]['src'] = self._regex_helper.group('SRC')
            self.current_ret[temp_pckt]['dst'] = self._regex_helper.group('DST')
            self.current_ret[temp_pckt]['proto'] = self._regex_helper.group('PROTO').strip()
            self.current_ret[temp_pckt]['id'] = self._regex_helper.group('ID')
            self.current_ret[temp_pckt]['seq'] = self._regex_helper.group('SEQ')
            self.current_ret[temp_pckt]['ttl'] = self._regex_helper.group('TTL')
            raise ParsingDone

    #     1 0.000000000          ::1 → ::1          ICMPv6 118 Echo (ping) request id=0x7b13, seq=4, hop limit=64
    _re_pckt_time_src_dst_proto_id_seq_hop_limit = re.compile(
        r"\s+(?P<PCKT>\d+)\s+(?P<TIME>\S+)\s+(?P<SRC>\S+)\s+[^A-Za-z0-9\s]\s+(?P<DST>\S+)\s+(?P<PROTO>.*)\s+id=(?P<ID>\S+),\s+seq=(?P<SEQ>\S+),\s+hop limit=(?P<HOP>\S+).*$")

    def _parse_pckt_time_src_dst_proto_id_seq_hop_limit(self, line):
        if self._regex_helper.search_compiled(Tshark._re_pckt_time_src_dst_proto_id_seq_hop_limit, line):
            temp_pckt = self._regex_helper.group('PCKT')
            self.current_ret[temp_pckt] = {}
            self.current_ret[temp_pckt]['time'] = self._regex_helper.group('TIME')
            self.current_ret[temp_pckt]['src'] = self._regex_helper.group('SRC')
            self.current_ret[temp_pckt]['dst'] = self._regex_helper.group('DST')
            self.current_ret[temp_pckt]['proto'] = self._regex_helper.group('PROTO').strip()
            self.current_ret[temp_pckt]['id'] = self._regex_helper.group('ID')
            self.current_ret[temp_pckt]['seq'] = self._regex_helper.group('SEQ')
            self.current_ret[temp_pckt]['hop_limit'] = self._regex_helper.group('HOP')
            raise ParsingDone

    # 9 packets captured
    _re_pckts_captured = re.compile(r"^(?P<PCKTS>\d+) packets captured$")

    def _parse_pckts_captured(self, line):
        if self._regex_helper.search_compiled(Tshark._re_pckts_captured, line):
            self.current_ret["packets_captured"] = self._regex_helper.group('PCKTS')
            raise ParsingDone


COMMAND_OUTPUT = """
ute@debdev:~/moler_int$ tshark -a duration:5 -i lo
Capturing on 'Loopback'
    1 0.000000000    127.0.0.1 → 127.0.0.1    ICMP 98 Echo (ping) request  id=0x693b, seq=48/12288, ttl=64
    2 0.000008132    127.0.0.1 → 127.0.0.1    ICMP 98 Echo (ping) reply    id=0x693b, seq=48/12288, ttl=64 (request in 1)
    3 1.000252666    127.0.0.1 → 127.0.0.1    ICMP 98 Echo (ping) request  id=0x693b, seq=49/12544, ttl=64
    4 1.000261422    127.0.0.1 → 127.0.0.1    ICMP 98 Echo (ping) reply    id=0x693b, seq=49/12544, ttl=64 (request in 3)
    5 2.000217517    127.0.0.1 → 127.0.0.1    ICMP 98 Echo (ping) request  id=0x693b, seq=50/12800, ttl=64
    6 2.000224442    127.0.0.1 → 127.0.0.1    ICMP 98 Echo (ping) reply    id=0x693b, seq=50/12800, ttl=64 (request in 5)
    7 2.999995357    127.0.0.1 → 127.0.0.1    ICMP 98 Echo (ping) request  id=0x693b, seq=51/13056, ttl=64
    8 3.000002132    127.0.0.1 → 127.0.0.1    ICMP 98 Echo (ping) reply    id=0x693b, seq=51/13056, ttl=64 (request in 7)
    9 4.000010976    127.0.0.1 → 127.0.0.1    ICMP 98 Echo (ping) request  id=0x693b, seq=52/13312, ttl=64
9 packets captured
ute@debdev:~/moler_int$"""
COMMAND_KWARGS = {
    'options': '-a duration:5 -i lo',
}
COMMAND_RESULT = {
    "packets_captured": "9",
    "1": {
        'time': '0.000000000',
        'src': '127.0.0.1',
        'dst': '127.0.0.1',
        'proto': 'ICMP 98 Echo (ping) request',
        'id': '0x693b',
        'seq': '48/12288',
        'ttl': '64',
    },
    "2": {
        'time': '0.000008132',
        'src': '127.0.0.1',
        'dst': '127.0.0.1',
        'proto': 'ICMP 98 Echo (ping) reply',
        'id': '0x693b',
        'seq': '48/12288',
        'ttl': '64',
    },
    "3": {
        'time': '1.000252666',
        'src': '127.0.0.1',
        'dst': '127.0.0.1',
        'proto': 'ICMP 98 Echo (ping) request',
        'id': '0x693b',
        'seq': '49/12544',
        'ttl': '64',
    },
    "4": {
        'time': '1.000261422',
        'src': '127.0.0.1',
        'dst': '127.0.0.1',
        'proto': 'ICMP 98 Echo (ping) reply',
        'id': '0x693b',
        'seq': '49/12544',
        'ttl': '64',
    },
    "5": {
        'time': '2.000217517',
        'src': '127.0.0.1',
        'dst': '127.0.0.1',
        'proto': 'ICMP 98 Echo (ping) request',
        'id': '0x693b',
        'seq': '50/12800',
        'ttl': '64',
    },
    "6": {
        'time': '2.000224442',
        'src': '127.0.0.1',
        'dst': '127.0.0.1',
        'proto': 'ICMP 98 Echo (ping) reply',
        'id': '0x693b',
        'seq': '50/12800',
        'ttl': '64',
    },
    "7": {
        'time': '2.999995357',
        'src': '127.0.0.1',
        'dst': '127.0.0.1',
        'proto': 'ICMP 98 Echo (ping) request',
        'id': '0x693b',
        'seq': '51/13056',
        'ttl': '64',
    },
    "8": {
        'time': '3.000002132',
        'src': '127.0.0.1',
        'dst': '127.0.0.1',
        'proto': 'ICMP 98 Echo (ping) reply',
        'id': '0x693b',
        'seq': '51/13056',
        'ttl': '64',
    },
    "9": {
        'time': '4.000010976',
        'src': '127.0.0.1',
        'dst': '127.0.0.1',
        'proto': 'ICMP 98 Echo (ping) request',
        'id': '0x693b',
        'seq': '52/13312',
        'ttl': '64',
    },
}

COMMAND_OUTPUT_v6 = """ute@debdev:~/moler_int$ tshark -a duration:5 -i lo
Capturing on 'Loopback'
    1 0.000000000          ::1 → ::1          ICMPv6 118 Echo (ping) request id=0x7b13, seq=4, hop limit=64
    2 0.000009358          ::1 → ::1          ICMPv6 118 Echo (ping) reply id=0x7b13, seq=4, hop limit=64 (request in 1)
    3 0.999730036          ::1 → ::1          ICMPv6 118 Echo (ping) request id=0x7b13, seq=5, hop limit=64
    4 0.999738770          ::1 → ::1          ICMPv6 118 Echo (ping) reply id=0x7b13, seq=5, hop limit=64 (request in 3)
    5 1.999820369          ::1 → ::1          ICMPv6 118 Echo (ping) request id=0x7b13, seq=6, hop limit=64
    6 1.999827821          ::1 → ::1          ICMPv6 118 Echo (ping) reply id=0x7b13, seq=6, hop limit=64 (request in 5)
    7 3.000413784          ::1 → ::1          ICMPv6 118 Echo (ping) request id=0x7b13, seq=7, hop limit=64
    8 3.000445708          ::1 → ::1          ICMPv6 118 Echo (ping) reply id=0x7b13, seq=7, hop limit=64 (request in 7)
    9 3.999585722          ::1 → ::1          ICMPv6 118 Echo (ping) request id=0x7b13, seq=8, hop limit=64
   10 3.999594594          ::1 → ::1          ICMPv6 118 Echo (ping) reply id=0x7b13, seq=8, hop limit=64 (request in 9)
10 packets captured
ute@debdev:~/moler_int$"""
COMMAND_KWARGS_v6 = {
    'options': '-a duration:5 -i lo',
}
COMMAND_RESULT_v6 = {
    "packets_captured": "10",
    "1": {
        'time': '0.000000000',
        'src': '::1',
        'dst': '::1',
        'proto': 'ICMPv6 118 Echo (ping) request',
        'id': '0x7b13',
        'seq': '4',
        'hop_limit': '64',
    },
    "2": {
        'time': '0.000009358',
        'src': '::1',
        'dst': '::1',
        'proto': 'ICMPv6 118 Echo (ping) reply',
        'id': '0x7b13',
        'seq': '4',
        'hop_limit': '64',
    },
    "3": {
        'time': '0.999730036',
        'src': '::1',
        'dst': '::1',
        'proto': 'ICMPv6 118 Echo (ping) request',
        'id': '0x7b13',
        'seq': '5',
        'hop_limit': '64',
    },
    "4": {
        'time': '0.999738770',
        'src': '::1',
        'dst': '::1',
        'proto': 'ICMPv6 118 Echo (ping) reply',
        'id': '0x7b13',
        'seq': '5',
        'hop_limit': '64',
    },
    "5": {
        'time': '1.999820369',
        'src': '::1',
        'dst': '::1',
        'proto': 'ICMPv6 118 Echo (ping) request',
        'id': '0x7b13',
        'seq': '6',
        'hop_limit': '64',
    },
    "6": {
        'time': '1.999827821',
        'src': '::1',
        'dst': '::1',
        'proto': 'ICMPv6 118 Echo (ping) reply',
        'id': '0x7b13',
        'seq': '6',
        'hop_limit': '64',
    },
    "7": {
        'time': '3.000413784',
        'src': '::1',
        'dst': '::1',
        'proto': 'ICMPv6 118 Echo (ping) request',
        'id': '0x7b13',
        'seq': '7',
        'hop_limit': '64',
    },
    "8": {
        'time': '3.000445708',
        'src': '::1',
        'dst': '::1',
        'proto': 'ICMPv6 118 Echo (ping) reply',
        'id': '0x7b13',
        'seq': '7',
        'hop_limit': '64',
    },
    "9": {
        'time': '3.999585722',
        'src': '::1',
        'dst': '::1',
        'proto': 'ICMPv6 118 Echo (ping) request',
        'id': '0x7b13',
        'seq': '8',
        'hop_limit': '64',
    },
    "10": {
        'time': '3.999594594',
        'src': '::1',
        'dst': '::1',
        'proto': 'ICMPv6 118 Echo (ping) reply',
        'id': '0x7b13',
        'seq': '8',
        'hop_limit': '64',
    },
}
