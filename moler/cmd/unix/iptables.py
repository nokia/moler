# -*- coding: utf-8 -*-
"""
iptables command module.
"""

__author__ = 'Sylwester Golonka'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'sylwester.golonka@nokia.com'

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone


class Iptables(GenericUnixCommand):
    def __init__(self, connection, options=None, v6=None, prompt=None, newline_chars=None, runner=None):
        super(Iptables, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                       runner=runner)
        self.options = options
        self.v6 = v6
        self.ret_required = False

        self.chain = None

    def build_command_string(self):
        cmd = "iptables"
        if self.v6:
            cmd = "ip6tables"
        if self.options:
            cmd = "{} {}".format(cmd, self.options)
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_chain(line)
                self._parse_chain_references(line)
                self._parse_headers(line)
                self._parse_details(line)
            except ParsingDone:
                pass
        return super(Iptables, self).on_new_line(line, is_full_line)

    # Chain INPUT (policy DROP 0 packets, 0 bytes)
    _re_parse_chain = re.compile(
        r"Chain\s+(?P<NAME>\S+)\s+\(policy\s(?P<POLICY>\S+)\s+(?P<PACKETS>\d+)\s+packets,\s+(?P<BYTES>\d+)\s+bytes\)$")

    def _parse_chain(self, line):
        if self._regex_helper.search_compiled(Iptables._re_parse_chain, line):
            self.chain = self._regex_helper.group("NAME")
            self.current_ret[self.chain] = dict()
            self.current_ret[self.chain]["POLICY"] = self._regex_helper.group("POLICY")
            self.current_ret[self.chain]["PACKETS"] = self._regex_helper.group("PACKETS")
            self.current_ret[self.chain]["BYTES"] = self._regex_helper.group("BYTES")
            self.current_ret[self.chain]["CHAIN"] = []
            raise ParsingDone

    # Chain CP_TRAFFIC_RATE_LIMIT (1 references)
    _re_parse_chain_references = re.compile(r"Chain\s+(?P<NAME>\S+)\s+\((?P<REFERENCES>\d+) references\)$")

    def _parse_chain_references(self, line):
        if self._regex_helper.search_compiled(Iptables._re_parse_chain_references, line):
            self.chain = self._regex_helper.group("NAME")
            self.current_ret[self.chain] = dict()
            self.current_ret[self.chain]["REFERENCES"] = self._regex_helper.group("REFERENCES")
            self.current_ret[self.chain]["CHAIN"] = []
            raise ParsingDone

    #    pkts      bytes target     prot opt in     out     source               destination
    _re_parse_headers = re.compile(r"(?P<HEADERS>pkts\s+bytes\s+target\s+prot\s+opt\s+in\s+out\s+source\s+destination)")

    def _parse_headers(self, line):
        if self._regex_helper.search_compiled(Iptables._re_parse_headers, line):
            raise ParsingDone

    #   0        0 ACCEPT     icmp --  *      *       0.0.0.0/0            0.0.0.0/0            icmptype 8 limit: avg 25/sec burst 5
    _re_parse_details = re.compile(r"\s+(?P<VALUE>\S+)")
    _re_parse_rest = re.compile(r"(?P<DETAIL>\s+\S+){9}\s+(?P<REST>.*)")
    _key_details = ["PKTS", "BYTES", "TARGET", "PROT", "OPT", "IN", "OUT", "SOURCE", "DESTINATION"]

    def _parse_details(self, line):
        if self._regex_helper.search_compiled(Iptables._re_parse_details, line):
            values = re.findall(Iptables._re_parse_details, line)
            ret = dict()
            for value, key in zip(values, Iptables._key_details):
                ret[key] = value
            self.current_ret[self.chain]["CHAIN"].append(ret)
        if self._regex_helper.search_compiled(Iptables._re_parse_rest, line):
            ret = dict()
            ret["REST"] = self._regex_helper.group("REST")
            self.current_ret[self.chain]["CHAIN"].append(ret)
            raise ParsingDone


COMMAND_OUTPUT = """
toor4nsn@fzm-lsp-k2:~# iptables -nvxL
Chain INPUT (policy DROP 12 packets, 3054 bytes)
    pkts      bytes target     prot opt in     out     source               destination
       0        0 DROP       all  --  *      *       0.0.0.0/0            0.0.0.0/0            u32 "0x0&0xf000000=0x6000000:0xf000000"
       0        0 ACCEPT     tcp  --  br0+   *       0.0.0.0/0            0.0.0.0/0            multiport dports 15010:15014 state RELATED,ESTABLISHED
       0        0 ACCEPT     all  --  eth4   *       0.0.0.0/0            0.0.0.0/0
       0        0 ACCEPT     udp  --  *      *       0.0.0.0/0            0.0.0.0/0            udp dpt:16009
       0        0 ACCEPT     esp  --  *      *       0.0.0.0/0            0.0.0.0/0
   17207 52497455 ACCEPT     all  --  lo     *       0.0.0.0/0            0.0.0.0/0
       0        0 ACCEPT     udp  --  *      *       0.0.0.0/0            0.0.0.0/0            udp spt:67 dpt:68 ctstate RELATED,ESTABLISHED
       0        0 DROP       all  --  *      *       0.0.0.0/0            0.0.0.0/0            u32 "0x0&0xf000000>>0x18=0x6:0xf"
       0        0 DROP       all  --  *      *       0.0.0.0/0            0.0.0.0/0            u32 "0x0&0xffff=0x3fe1:0xffff"
       0        0 DROP       tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp dpt:21
      12     3054 ACCEPT     all  --  eth1+  *       192.168.255.0/24     0.0.0.0/0
       0        0 ACCEPT     udp  --  *      *       0.0.0.0/0            0.0.0.0/0            udp dpts:5001:5010 ctstate RELATED,ESTABLISHED
       0        0 UDP_ECHO_REQUEST_RATE_LIMIT  udp  --  *      *       0.0.0.0/0            0.0.0.0/0            udp spts:5001:5010
       0        0 DROP       udp  --  *      *       0.0.0.0/0            0.0.0.0/0            udp spt:7 dpt:7
       0        0 ACCEPT     udp  --  *      *       0.0.0.0/0            0.0.0.0/0            udp dpts:33434:33933 ADDRTYPE match dst-type LOCAL
       0        0 INGRESS_ICMP  icmp --  br0+   *       0.0.0.0/0            0.0.0.0/0
       0        0 ACCEPT     udp  --  br0+   *       0.0.0.0/0            10.0.0.248           udp dpt:2152
       0        0 ACCEPT     udp  --  br0+   *       0.0.0.0/0            10.0.111.248         udp dpt:2152
      13      468 CP_TRAFFIC_RATE_LIMIT  sctp --  br0+   *       0.0.0.0/0            10.0.0.248
       0        0 ACCEPT     udp  --  *      *       0.0.0.0/0            10.0.0.248           udp dpt:500
       0        0 ACCEPT     udp  --  *      *       0.0.0.0/0            10.0.111.248         udp dpt:500
     254    15621 MP_TRAFFIC  all  --  *      *       0.0.0.0/0            10.1.52.248
       0        0 MP_TRAFFIC_RATE_LIMIT  tcp  --  *      *       10.83.225.1          0.0.0.0/0            tcp spt:389 ctstate RELATED,ESTABLISHED
       0        0 ACCEPT     tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            multiport dports 15001:15005,15007
       0        0 ACCEPT     tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp dpt:22

Chain FORWARD (policy DROP 0 packets, 0 bytes)
    pkts      bytes target     prot opt in     out     source               destination
       0        0 MP_TRAFFIC_RATE_LIMIT  udp  --  *      *       10.1.52.248          0.0.0.0/0            multiport sports 13080:13099,13120:13140
       0        0 MP_TRAFFIC_RATE_LIMIT  tcp  --  *      *       10.1.52.248          0.0.0.0/0            multiport sports 15008,15010:15029

Chain OUTPUT (policy ACCEPT 50759 packets, 87055714 bytes)
    pkts      bytes target     prot opt in     out     source               destination
   38592 18743328 EGRESS_ICMP  icmp --  *      *       0.0.0.0/0            0.0.0.0/0

Chain CP_TRAFFIC_RATE_LIMIT (1 references)
    pkts      bytes target     prot opt in     out     source               destination
      13      468 ACCEPT     sctp --  *      *       0.0.0.0/0            0.0.0.0/0            limit: avg 2000/sec burst 80
       0        0 DROP       sctp --  *      *       0.0.0.0/0            0.0.0.0/0

Chain DISCARD_CHAIN (2 references)
    pkts      bytes target     prot opt in     out     source               destination
       0        0 DROP       all  --  *      *       0.0.0.0/0            0.0.0.0/0

Chain EGRESS_ICMP (1 references)
    pkts      bytes target     prot opt in     out     source               destination
       0        0 EGRESS_ICMP_RATE_LIMIT  icmp --  *      *       0.0.0.0/0            0.0.0.0/0            icmptype 8 ctstate NEW,ESTABLISHED
       0        0 EGRESS_ICMP_RATE_LIMIT  icmp --  *      *       0.0.0.0/0            0.0.0.0/0            icmptype 0 ctstate ESTABLISHED
   38592 18743328 EGRESS_ICMP_RATE_LIMIT  icmp --  *      *       0.0.0.0/0            0.0.0.0/0            icmptype 3
       0        0 EGRESS_ICMP_RATE_LIMIT  icmp --  *      *       0.0.0.0/0            0.0.0.0/0            icmptype 11
       0        0 ACCEPT     icmp --  *      *       0.0.0.0/0            0.0.0.0/0            icmptype 12
       0        0 DISCARD_CHAIN  icmp --  *      *       0.0.0.0/0            0.0.0.0/0

Chain EGRESS_ICMP_RATE_LIMIT (4 references)
    pkts      bytes target     prot opt in     out     source               destination
       0        0 ACCEPT     icmp --  *      *       0.0.0.0/0            0.0.0.0/0            icmptype 8 limit: avg 25/sec burst 5
       0        0 ACCEPT     icmp --  *      *       0.0.0.0/0            0.0.0.0/0            icmptype 0 limit: avg 25/sec burst 5
    6101  2834715 ACCEPT     icmp --  *      *       0.0.0.0/0            0.0.0.0/0            icmptype 3 limit: avg 25/sec burst 5
       0        0 ACCEPT     icmp --  *      *       0.0.0.0/0            0.0.0.0/0            icmptype 11 limit: avg 25/sec burst 5
   32491 15908613 DROP       icmp --  *      *       0.0.0.0/0            0.0.0.0/0

Chain INGRESS_ICMP (1 references)
    pkts      bytes target     prot opt in     out     source               destination
       0        0 INGRESS_ICMP_RATE_LIMIT  icmp --  *      *       0.0.0.0/0            0.0.0.0/0            icmptype 8 ctstate NEW,ESTABLISHED
       0        0 INGRESS_ICMP_RATE_LIMIT  icmp --  *      *       0.0.0.0/0            0.0.0.0/0            icmptype 0 ctstate ESTABLISHED
       0        0 ACCEPT     icmp --  *      *       0.0.0.0/0            0.0.0.0/0            icmptype 3
       0        0 ACCEPT     icmp --  *      *       0.0.0.0/0            0.0.0.0/0            icmptype 11
       0        0 ACCEPT     icmp --  *      *       0.0.0.0/0            0.0.0.0/0            icmptype 12
       0        0 DISCARD_CHAIN  icmp --  *      *       0.0.0.0/0            0.0.0.0/0

Chain INGRESS_ICMP_RATE_LIMIT (2 references)
    pkts      bytes target     prot opt in     out     source               destination
       0        0 ACCEPT     icmp --  *      *       0.0.0.0/0            0.0.0.0/0            icmptype 8 limit: avg 25/sec burst 8
       0        0 ACCEPT     icmp --  *      *       0.0.0.0/0            0.0.0.0/0            icmptype 0 limit: avg 25/sec burst 8
       0        0 DROP       icmp --  *      *       0.0.0.0/0            0.0.0.0/0

Chain MP_TRAFFIC (1 references)
    pkts      bytes target     prot opt in     out     source               destination
       0        0 MP_TRAFFIC_RATE_LIMIT  udp  --  *      *       0.0.0.0/0            0.0.0.0/0            udp spt:53 ctstate RELATED,ESTABLISHED
       0        0 MP_TRAFFIC_RATE_LIMIT  tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp spt:53 ctstate RELATED,ESTABLISHED
       0        0 MP_TRAFFIC_RATE_LIMIT  tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp spt:21 ctstate RELATED,ESTABLISHED
       0        0 MP_TRAFFIC_RATE_LIMIT  tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp spt:20 dpts:1024:65535 ctstate RELATED,ESTABLISHED
       0        0 MP_TRAFFIC_RATE_LIMIT  tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp spt:22 dpts:1024:65535 ctstate RELATED,ESTABLISHED
       0        0 MP_TRAFFIC_RATE_LIMIT  tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp spt:23 dpts:1024:65535 ctstate RELATED,ESTABLISHED
     254    15621 MP_TRAFFIC_RATE_LIMIT  tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            ctstate RELATED,ESTABLISHED
       0        0 MP_TRAFFIC_RATE_LIMIT  tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            multiport dports 6001,443
       0        0 MP_TRAFFIC_RATE_LIMIT  tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp dpt:6000
       0        0 MP_TRAFFIC_RATE_LIMIT  tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            multiport sports 8002,8003 ctstate RELATED,ESTABLISHED
       0        0 MP_TRAFFIC_RATE_LIMIT  udp  --  *      *       10.83.225.254        0.0.0.0/0            udp spt:123 dpt:123
       0        0 MP_TRAFFIC_RATE_LIMIT  tcp  --  *      *       10.83.224.100        0.0.0.0/0            tcp spt:8080
       0        0 ACCEPT     tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp dpt:12000 state NEW

Chain MP_TRAFFIC_RATE_LIMIT (15 references)
    pkts      bytes target     prot opt in     out     source               destination
     254    15621 ACCEPT     all  --  *      *       0.0.0.0/0            0.0.0.0/0            limit: avg 2000/sec burst 32
       0        0 DROP       all  --  *      *       0.0.0.0/0            0.0.0.0/0

Chain TLS_RENEG_RATE_LIMIT (0 references)
    pkts      bytes target     prot opt in     out     source               destination

Chain TOP_TRAFFIC_RATE_LIMIT (0 references)
    pkts      bytes target     prot opt in     out     source               destination

Chain UDP_ECHO_REQUEST_RATE_LIMIT (1 references)
    pkts      bytes target     prot opt in     out     source               destination
       0        0 ACCEPT     all  --  *      *       0.0.0.0/0            0.0.0.0/0            limit: avg 100/sec burst 5
       0        0 DROP       all  --  *      *       0.0.0.0/0            0.0.0.0/0
toor4nsn@fzm-lsp-k2:~#"""

COMMAND_KWARGS = {'options': '-nvxL'}

COMMAND_RESULT = {u'CP_TRAFFIC_RATE_LIMIT': {'CHAIN': [{'BYTES': u'468',
                                                        'DESTINATION': u'0.0.0.0/0',
                                                        'IN': u'*',
                                                        'OPT': u'--',
                                                        'OUT': u'*',
                                                        'PKTS': u'13',
                                                        'PROT': u'sctp',
                                                        'SOURCE': u'0.0.0.0/0',
                                                        'TARGET': u'ACCEPT'},
                                                       {'REST': u'limit: avg 2000/sec burst 80'},
                                                       {'BYTES': u'0',
                                                        'DESTINATION': u'0.0.0.0/0',
                                                        'IN': u'*',
                                                        'OPT': u'--',
                                                        'OUT': u'*',
                                                        'PKTS': u'0',
                                                        'PROT': u'sctp',
                                                        'SOURCE': u'0.0.0.0/0',
                                                        'TARGET': u'DROP'}],
                                             'REFERENCES': u'1'},
                  u'DISCARD_CHAIN': {'CHAIN': [{'BYTES': u'0',
                                                'DESTINATION': u'0.0.0.0/0',
                                                'IN': u'*',
                                                'OPT': u'--',
                                                'OUT': u'*',
                                                'PKTS': u'0',
                                                'PROT': u'all',
                                                'SOURCE': u'0.0.0.0/0',
                                                'TARGET': u'DROP'}],
                                     'REFERENCES': u'2'},
                  u'EGRESS_ICMP': {'CHAIN': [{'BYTES': u'0',
                                              'DESTINATION': u'0.0.0.0/0',
                                              'IN': u'*',
                                              'OPT': u'--',
                                              'OUT': u'*',
                                              'PKTS': u'0',
                                              'PROT': u'icmp',
                                              'SOURCE': u'0.0.0.0/0',
                                              'TARGET': u'EGRESS_ICMP_RATE_LIMIT'},
                                             {'REST': u'icmptype 8 ctstate NEW,ESTABLISHED'},
                                             {'BYTES': u'0',
                                              'DESTINATION': u'0.0.0.0/0',
                                              'IN': u'*',
                                              'OPT': u'--',
                                              'OUT': u'*',
                                              'PKTS': u'0',
                                              'PROT': u'icmp',
                                              'SOURCE': u'0.0.0.0/0',
                                              'TARGET': u'EGRESS_ICMP_RATE_LIMIT'},
                                             {'REST': u'icmptype 0 ctstate ESTABLISHED'},
                                             {'BYTES': u'18743328',
                                              'DESTINATION': u'0.0.0.0/0',
                                              'IN': u'*',
                                              'OPT': u'--',
                                              'OUT': u'*',
                                              'PKTS': u'38592',
                                              'PROT': u'icmp',
                                              'SOURCE': u'0.0.0.0/0',
                                              'TARGET': u'EGRESS_ICMP_RATE_LIMIT'},
                                             {'REST': u'icmptype 3'},
                                             {'BYTES': u'0',
                                              'DESTINATION': u'0.0.0.0/0',
                                              'IN': u'*',
                                              'OPT': u'--',
                                              'OUT': u'*',
                                              'PKTS': u'0',
                                              'PROT': u'icmp',
                                              'SOURCE': u'0.0.0.0/0',
                                              'TARGET': u'EGRESS_ICMP_RATE_LIMIT'},
                                             {'REST': u'icmptype 11'},
                                             {'BYTES': u'0',
                                              'DESTINATION': u'0.0.0.0/0',
                                              'IN': u'*',
                                              'OPT': u'--',
                                              'OUT': u'*',
                                              'PKTS': u'0',
                                              'PROT': u'icmp',
                                              'SOURCE': u'0.0.0.0/0',
                                              'TARGET': u'ACCEPT'},
                                             {'REST': u'icmptype 12'},
                                             {'BYTES': u'0',
                                              'DESTINATION': u'0.0.0.0/0',
                                              'IN': u'*',
                                              'OPT': u'--',
                                              'OUT': u'*',
                                              'PKTS': u'0',
                                              'PROT': u'icmp',
                                              'SOURCE': u'0.0.0.0/0',
                                              'TARGET': u'DISCARD_CHAIN'}],
                                   'REFERENCES': u'1'},
                  u'EGRESS_ICMP_RATE_LIMIT': {'CHAIN': [{'BYTES': u'0',
                                                         'DESTINATION': u'0.0.0.0/0',
                                                         'IN': u'*',
                                                         'OPT': u'--',
                                                         'OUT': u'*',
                                                         'PKTS': u'0',
                                                         'PROT': u'icmp',
                                                         'SOURCE': u'0.0.0.0/0',
                                                         'TARGET': u'ACCEPT'},
                                                        {'REST': u'icmptype 8 limit: avg 25/sec burst 5'},
                                                        {'BYTES': u'0',
                                                         'DESTINATION': u'0.0.0.0/0',
                                                         'IN': u'*',
                                                         'OPT': u'--',
                                                         'OUT': u'*',
                                                         'PKTS': u'0',
                                                         'PROT': u'icmp',
                                                         'SOURCE': u'0.0.0.0/0',
                                                         'TARGET': u'ACCEPT'},
                                                        {'REST': u'icmptype 0 limit: avg 25/sec burst 5'},
                                                        {'BYTES': u'2834715',
                                                         'DESTINATION': u'0.0.0.0/0',
                                                         'IN': u'*',
                                                         'OPT': u'--',
                                                         'OUT': u'*',
                                                         'PKTS': u'6101',
                                                         'PROT': u'icmp',
                                                         'SOURCE': u'0.0.0.0/0',
                                                         'TARGET': u'ACCEPT'},
                                                        {'REST': u'icmptype 3 limit: avg 25/sec burst 5'},
                                                        {'BYTES': u'0',
                                                         'DESTINATION': u'0.0.0.0/0',
                                                         'IN': u'*',
                                                         'OPT': u'--',
                                                         'OUT': u'*',
                                                         'PKTS': u'0',
                                                         'PROT': u'icmp',
                                                         'SOURCE': u'0.0.0.0/0',
                                                         'TARGET': u'ACCEPT'},
                                                        {'REST': u'icmptype 11 limit: avg 25/sec burst 5'},
                                                        {'BYTES': u'15908613',
                                                         'DESTINATION': u'0.0.0.0/0',
                                                         'IN': u'*',
                                                         'OPT': u'--',
                                                         'OUT': u'*',
                                                         'PKTS': u'32491',
                                                         'PROT': u'icmp',
                                                         'SOURCE': u'0.0.0.0/0',
                                                         'TARGET': u'DROP'}],
                                              'REFERENCES': u'4'},
                  u'FORWARD': {'BYTES': u'0',
                               'CHAIN': [{'BYTES': u'0',
                                          'DESTINATION': u'0.0.0.0/0',
                                          'IN': u'*',
                                          'OPT': u'--',
                                          'OUT': u'*',
                                          'PKTS': u'0',
                                          'PROT': u'udp',
                                          'SOURCE': u'10.1.52.248',
                                          'TARGET': u'MP_TRAFFIC_RATE_LIMIT'},
                                         {'REST': u'multiport sports 13080:13099,13120:13140'},
                                         {'BYTES': u'0',
                                          'DESTINATION': u'0.0.0.0/0',
                                          'IN': u'*',
                                          'OPT': u'--',
                                          'OUT': u'*',
                                          'PKTS': u'0',
                                          'PROT': u'tcp',
                                          'SOURCE': u'10.1.52.248',
                                          'TARGET': u'MP_TRAFFIC_RATE_LIMIT'},
                                         {'REST': u'multiport sports 15008,15010:15029'}],
                               'PACKETS': u'0',
                               'POLICY': u'DROP'},
                  u'INGRESS_ICMP': {'CHAIN': [{'BYTES': u'0',
                                               'DESTINATION': u'0.0.0.0/0',
                                               'IN': u'*',
                                               'OPT': u'--',
                                               'OUT': u'*',
                                               'PKTS': u'0',
                                               'PROT': u'icmp',
                                               'SOURCE': u'0.0.0.0/0',
                                               'TARGET': u'INGRESS_ICMP_RATE_LIMIT'},
                                              {'REST': u'icmptype 8 ctstate NEW,ESTABLISHED'},
                                              {'BYTES': u'0',
                                               'DESTINATION': u'0.0.0.0/0',
                                               'IN': u'*',
                                               'OPT': u'--',
                                               'OUT': u'*',
                                               'PKTS': u'0',
                                               'PROT': u'icmp',
                                               'SOURCE': u'0.0.0.0/0',
                                               'TARGET': u'INGRESS_ICMP_RATE_LIMIT'},
                                              {'REST': u'icmptype 0 ctstate ESTABLISHED'},
                                              {'BYTES': u'0',
                                               'DESTINATION': u'0.0.0.0/0',
                                               'IN': u'*',
                                               'OPT': u'--',
                                               'OUT': u'*',
                                               'PKTS': u'0',
                                               'PROT': u'icmp',
                                               'SOURCE': u'0.0.0.0/0',
                                               'TARGET': u'ACCEPT'},
                                              {'REST': u'icmptype 3'},
                                              {'BYTES': u'0',
                                               'DESTINATION': u'0.0.0.0/0',
                                               'IN': u'*',
                                               'OPT': u'--',
                                               'OUT': u'*',
                                               'PKTS': u'0',
                                               'PROT': u'icmp',
                                               'SOURCE': u'0.0.0.0/0',
                                               'TARGET': u'ACCEPT'},
                                              {'REST': u'icmptype 11'},
                                              {'BYTES': u'0',
                                               'DESTINATION': u'0.0.0.0/0',
                                               'IN': u'*',
                                               'OPT': u'--',
                                               'OUT': u'*',
                                               'PKTS': u'0',
                                               'PROT': u'icmp',
                                               'SOURCE': u'0.0.0.0/0',
                                               'TARGET': u'ACCEPT'},
                                              {'REST': u'icmptype 12'},
                                              {'BYTES': u'0',
                                               'DESTINATION': u'0.0.0.0/0',
                                               'IN': u'*',
                                               'OPT': u'--',
                                               'OUT': u'*',
                                               'PKTS': u'0',
                                               'PROT': u'icmp',
                                               'SOURCE': u'0.0.0.0/0',
                                               'TARGET': u'DISCARD_CHAIN'}],
                                    'REFERENCES': u'1'},
                  u'INGRESS_ICMP_RATE_LIMIT': {'CHAIN': [{'BYTES': u'0',
                                                          'DESTINATION': u'0.0.0.0/0',
                                                          'IN': u'*',
                                                          'OPT': u'--',
                                                          'OUT': u'*',
                                                          'PKTS': u'0',
                                                          'PROT': u'icmp',
                                                          'SOURCE': u'0.0.0.0/0',
                                                          'TARGET': u'ACCEPT'},
                                                         {'REST': u'icmptype 8 limit: avg 25/sec burst 8'},
                                                         {'BYTES': u'0',
                                                          'DESTINATION': u'0.0.0.0/0',
                                                          'IN': u'*',
                                                          'OPT': u'--',
                                                          'OUT': u'*',
                                                          'PKTS': u'0',
                                                          'PROT': u'icmp',
                                                          'SOURCE': u'0.0.0.0/0',
                                                          'TARGET': u'ACCEPT'},
                                                         {'REST': u'icmptype 0 limit: avg 25/sec burst 8'},
                                                         {'BYTES': u'0',
                                                          'DESTINATION': u'0.0.0.0/0',
                                                          'IN': u'*',
                                                          'OPT': u'--',
                                                          'OUT': u'*',
                                                          'PKTS': u'0',
                                                          'PROT': u'icmp',
                                                          'SOURCE': u'0.0.0.0/0',
                                                          'TARGET': u'DROP'}],
                                               'REFERENCES': u'2'},
                  u'INPUT': {'BYTES': u'3054',
                             'CHAIN': [{'BYTES': u'0',
                                        'DESTINATION': u'0.0.0.0/0',
                                        'IN': u'*',
                                        'OPT': u'--',
                                        'OUT': u'*',
                                        'PKTS': u'0',
                                        'PROT': u'all',
                                        'SOURCE': u'0.0.0.0/0',
                                        'TARGET': u'DROP'},
                                       {'REST': u'u32 "0x0&0xf000000=0x6000000:0xf000000"'},
                                       {'BYTES': u'0',
                                        'DESTINATION': u'0.0.0.0/0',
                                        'IN': u'br0+',
                                        'OPT': u'--',
                                        'OUT': u'*',
                                        'PKTS': u'0',
                                        'PROT': u'tcp',
                                        'SOURCE': u'0.0.0.0/0',
                                        'TARGET': u'ACCEPT'},
                                       {'REST': u'multiport dports 15010:15014 state RELATED,ESTABLISHED'},
                                       {'BYTES': u'0',
                                        'DESTINATION': u'0.0.0.0/0',
                                        'IN': u'eth4',
                                        'OPT': u'--',
                                        'OUT': u'*',
                                        'PKTS': u'0',
                                        'PROT': u'all',
                                        'SOURCE': u'0.0.0.0/0',
                                        'TARGET': u'ACCEPT'},
                                       {'BYTES': u'0',
                                        'DESTINATION': u'0.0.0.0/0',
                                        'IN': u'*',
                                        'OPT': u'--',
                                        'OUT': u'*',
                                        'PKTS': u'0',
                                        'PROT': u'udp',
                                        'SOURCE': u'0.0.0.0/0',
                                        'TARGET': u'ACCEPT'},
                                       {'REST': u'udp dpt:16009'},
                                       {'BYTES': u'0',
                                        'DESTINATION': u'0.0.0.0/0',
                                        'IN': u'*',
                                        'OPT': u'--',
                                        'OUT': u'*',
                                        'PKTS': u'0',
                                        'PROT': u'esp',
                                        'SOURCE': u'0.0.0.0/0',
                                        'TARGET': u'ACCEPT'},
                                       {'BYTES': u'52497455',
                                        'DESTINATION': u'0.0.0.0/0',
                                        'IN': u'lo',
                                        'OPT': u'--',
                                        'OUT': u'*',
                                        'PKTS': u'17207',
                                        'PROT': u'all',
                                        'SOURCE': u'0.0.0.0/0',
                                        'TARGET': u'ACCEPT'},
                                       {'BYTES': u'0',
                                        'DESTINATION': u'0.0.0.0/0',
                                        'IN': u'*',
                                        'OPT': u'--',
                                        'OUT': u'*',
                                        'PKTS': u'0',
                                        'PROT': u'udp',
                                        'SOURCE': u'0.0.0.0/0',
                                        'TARGET': u'ACCEPT'},
                                       {'REST': u'udp spt:67 dpt:68 ctstate RELATED,ESTABLISHED'},
                                       {'BYTES': u'0',
                                        'DESTINATION': u'0.0.0.0/0',
                                        'IN': u'*',
                                        'OPT': u'--',
                                        'OUT': u'*',
                                        'PKTS': u'0',
                                        'PROT': u'all',
                                        'SOURCE': u'0.0.0.0/0',
                                        'TARGET': u'DROP'},
                                       {'REST': u'u32 "0x0&0xf000000>>0x18=0x6:0xf"'},
                                       {'BYTES': u'0',
                                        'DESTINATION': u'0.0.0.0/0',
                                        'IN': u'*',
                                        'OPT': u'--',
                                        'OUT': u'*',
                                        'PKTS': u'0',
                                        'PROT': u'all',
                                        'SOURCE': u'0.0.0.0/0',
                                        'TARGET': u'DROP'},
                                       {'REST': u'u32 "0x0&0xffff=0x3fe1:0xffff"'},
                                       {'BYTES': u'0',
                                        'DESTINATION': u'0.0.0.0/0',
                                        'IN': u'*',
                                        'OPT': u'--',
                                        'OUT': u'*',
                                        'PKTS': u'0',
                                        'PROT': u'tcp',
                                        'SOURCE': u'0.0.0.0/0',
                                        'TARGET': u'DROP'},
                                       {'REST': u'tcp dpt:21'},
                                       {'BYTES': u'3054',
                                        'DESTINATION': u'0.0.0.0/0',
                                        'IN': u'eth1+',
                                        'OPT': u'--',
                                        'OUT': u'*',
                                        'PKTS': u'12',
                                        'PROT': u'all',
                                        'SOURCE': u'192.168.255.0/24',
                                        'TARGET': u'ACCEPT'},
                                       {'BYTES': u'0',
                                        'DESTINATION': u'0.0.0.0/0',
                                        'IN': u'*',
                                        'OPT': u'--',
                                        'OUT': u'*',
                                        'PKTS': u'0',
                                        'PROT': u'udp',
                                        'SOURCE': u'0.0.0.0/0',
                                        'TARGET': u'ACCEPT'},
                                       {'REST': u'udp dpts:5001:5010 ctstate RELATED,ESTABLISHED'},
                                       {'BYTES': u'0',
                                        'DESTINATION': u'0.0.0.0/0',
                                        'IN': u'*',
                                        'OPT': u'--',
                                        'OUT': u'*',
                                        'PKTS': u'0',
                                        'PROT': u'udp',
                                        'SOURCE': u'0.0.0.0/0',
                                        'TARGET': u'UDP_ECHO_REQUEST_RATE_LIMIT'},
                                       {'REST': u'udp spts:5001:5010'},
                                       {'BYTES': u'0',
                                        'DESTINATION': u'0.0.0.0/0',
                                        'IN': u'*',
                                        'OPT': u'--',
                                        'OUT': u'*',
                                        'PKTS': u'0',
                                        'PROT': u'udp',
                                        'SOURCE': u'0.0.0.0/0',
                                        'TARGET': u'DROP'},
                                       {'REST': u'udp spt:7 dpt:7'},
                                       {'BYTES': u'0',
                                        'DESTINATION': u'0.0.0.0/0',
                                        'IN': u'*',
                                        'OPT': u'--',
                                        'OUT': u'*',
                                        'PKTS': u'0',
                                        'PROT': u'udp',
                                        'SOURCE': u'0.0.0.0/0',
                                        'TARGET': u'ACCEPT'},
                                       {'REST': u'udp dpts:33434:33933 ADDRTYPE match dst-type LOCAL'},
                                       {'BYTES': u'0',
                                        'DESTINATION': u'0.0.0.0/0',
                                        'IN': u'br0+',
                                        'OPT': u'--',
                                        'OUT': u'*',
                                        'PKTS': u'0',
                                        'PROT': u'icmp',
                                        'SOURCE': u'0.0.0.0/0',
                                        'TARGET': u'INGRESS_ICMP'},
                                       {'BYTES': u'0',
                                        'DESTINATION': u'10.0.0.248',
                                        'IN': u'br0+',
                                        'OPT': u'--',
                                        'OUT': u'*',
                                        'PKTS': u'0',
                                        'PROT': u'udp',
                                        'SOURCE': u'0.0.0.0/0',
                                        'TARGET': u'ACCEPT'},
                                       {'REST': u'udp dpt:2152'},
                                       {'BYTES': u'0',
                                        'DESTINATION': u'10.0.111.248',
                                        'IN': u'br0+',
                                        'OPT': u'--',
                                        'OUT': u'*',
                                        'PKTS': u'0',
                                        'PROT': u'udp',
                                        'SOURCE': u'0.0.0.0/0',
                                        'TARGET': u'ACCEPT'},
                                       {'REST': u'udp dpt:2152'},
                                       {'BYTES': u'468',
                                        'DESTINATION': u'10.0.0.248',
                                        'IN': u'br0+',
                                        'OPT': u'--',
                                        'OUT': u'*',
                                        'PKTS': u'13',
                                        'PROT': u'sctp',
                                        'SOURCE': u'0.0.0.0/0',
                                        'TARGET': u'CP_TRAFFIC_RATE_LIMIT'},
                                       {'BYTES': u'0',
                                        'DESTINATION': u'10.0.0.248',
                                        'IN': u'*',
                                        'OPT': u'--',
                                        'OUT': u'*',
                                        'PKTS': u'0',
                                        'PROT': u'udp',
                                        'SOURCE': u'0.0.0.0/0',
                                        'TARGET': u'ACCEPT'},
                                       {'REST': u'udp dpt:500'},
                                       {'BYTES': u'0',
                                        'DESTINATION': u'10.0.111.248',
                                        'IN': u'*',
                                        'OPT': u'--',
                                        'OUT': u'*',
                                        'PKTS': u'0',
                                        'PROT': u'udp',
                                        'SOURCE': u'0.0.0.0/0',
                                        'TARGET': u'ACCEPT'},
                                       {'REST': u'udp dpt:500'},
                                       {'BYTES': u'15621',
                                        'DESTINATION': u'10.1.52.248',
                                        'IN': u'*',
                                        'OPT': u'--',
                                        'OUT': u'*',
                                        'PKTS': u'254',
                                        'PROT': u'all',
                                        'SOURCE': u'0.0.0.0/0',
                                        'TARGET': u'MP_TRAFFIC'},
                                       {'BYTES': u'0',
                                        'DESTINATION': u'0.0.0.0/0',
                                        'IN': u'*',
                                        'OPT': u'--',
                                        'OUT': u'*',
                                        'PKTS': u'0',
                                        'PROT': u'tcp',
                                        'SOURCE': u'10.83.225.1',
                                        'TARGET': u'MP_TRAFFIC_RATE_LIMIT'},
                                       {'REST': u'tcp spt:389 ctstate RELATED,ESTABLISHED'},
                                       {'BYTES': u'0',
                                        'DESTINATION': u'0.0.0.0/0',
                                        'IN': u'*',
                                        'OPT': u'--',
                                        'OUT': u'*',
                                        'PKTS': u'0',
                                        'PROT': u'tcp',
                                        'SOURCE': u'0.0.0.0/0',
                                        'TARGET': u'ACCEPT'},
                                       {'REST': u'multiport dports 15001:15005,15007'},
                                       {'BYTES': u'0',
                                        'DESTINATION': u'0.0.0.0/0',
                                        'IN': u'*',
                                        'OPT': u'--',
                                        'OUT': u'*',
                                        'PKTS': u'0',
                                        'PROT': u'tcp',
                                        'SOURCE': u'0.0.0.0/0',
                                        'TARGET': u'ACCEPT'},
                                       {'REST': u'tcp dpt:22'}],
                             'PACKETS': u'12',
                             'POLICY': u'DROP'},
                  u'MP_TRAFFIC': {'CHAIN': [{'BYTES': u'0',
                                             'DESTINATION': u'0.0.0.0/0',
                                             'IN': u'*',
                                             'OPT': u'--',
                                             'OUT': u'*',
                                             'PKTS': u'0',
                                             'PROT': u'udp',
                                             'SOURCE': u'0.0.0.0/0',
                                             'TARGET': u'MP_TRAFFIC_RATE_LIMIT'},
                                            {'REST': u'udp spt:53 ctstate RELATED,ESTABLISHED'},
                                            {'BYTES': u'0',
                                             'DESTINATION': u'0.0.0.0/0',
                                             'IN': u'*',
                                             'OPT': u'--',
                                             'OUT': u'*',
                                             'PKTS': u'0',
                                             'PROT': u'tcp',
                                             'SOURCE': u'0.0.0.0/0',
                                             'TARGET': u'MP_TRAFFIC_RATE_LIMIT'},
                                            {'REST': u'tcp spt:53 ctstate RELATED,ESTABLISHED'},
                                            {'BYTES': u'0',
                                             'DESTINATION': u'0.0.0.0/0',
                                             'IN': u'*',
                                             'OPT': u'--',
                                             'OUT': u'*',
                                             'PKTS': u'0',
                                             'PROT': u'tcp',
                                             'SOURCE': u'0.0.0.0/0',
                                             'TARGET': u'MP_TRAFFIC_RATE_LIMIT'},
                                            {'REST': u'tcp spt:21 ctstate RELATED,ESTABLISHED'},
                                            {'BYTES': u'0',
                                             'DESTINATION': u'0.0.0.0/0',
                                             'IN': u'*',
                                             'OPT': u'--',
                                             'OUT': u'*',
                                             'PKTS': u'0',
                                             'PROT': u'tcp',
                                             'SOURCE': u'0.0.0.0/0',
                                             'TARGET': u'MP_TRAFFIC_RATE_LIMIT'},
                                            {'REST': u'tcp spt:20 dpts:1024:65535 ctstate RELATED,ESTABLISHED'},
                                            {'BYTES': u'0',
                                             'DESTINATION': u'0.0.0.0/0',
                                             'IN': u'*',
                                             'OPT': u'--',
                                             'OUT': u'*',
                                             'PKTS': u'0',
                                             'PROT': u'tcp',
                                             'SOURCE': u'0.0.0.0/0',
                                             'TARGET': u'MP_TRAFFIC_RATE_LIMIT'},
                                            {'REST': u'tcp spt:22 dpts:1024:65535 ctstate RELATED,ESTABLISHED'},
                                            {'BYTES': u'0',
                                             'DESTINATION': u'0.0.0.0/0',
                                             'IN': u'*',
                                             'OPT': u'--',
                                             'OUT': u'*',
                                             'PKTS': u'0',
                                             'PROT': u'tcp',
                                             'SOURCE': u'0.0.0.0/0',
                                             'TARGET': u'MP_TRAFFIC_RATE_LIMIT'},
                                            {'REST': u'tcp spt:23 dpts:1024:65535 ctstate RELATED,ESTABLISHED'},
                                            {'BYTES': u'15621',
                                             'DESTINATION': u'0.0.0.0/0',
                                             'IN': u'*',
                                             'OPT': u'--',
                                             'OUT': u'*',
                                             'PKTS': u'254',
                                             'PROT': u'tcp',
                                             'SOURCE': u'0.0.0.0/0',
                                             'TARGET': u'MP_TRAFFIC_RATE_LIMIT'},
                                            {'REST': u'ctstate RELATED,ESTABLISHED'},
                                            {'BYTES': u'0',
                                             'DESTINATION': u'0.0.0.0/0',
                                             'IN': u'*',
                                             'OPT': u'--',
                                             'OUT': u'*',
                                             'PKTS': u'0',
                                             'PROT': u'tcp',
                                             'SOURCE': u'0.0.0.0/0',
                                             'TARGET': u'MP_TRAFFIC_RATE_LIMIT'},
                                            {'REST': u'multiport dports 6001,443'},
                                            {'BYTES': u'0',
                                             'DESTINATION': u'0.0.0.0/0',
                                             'IN': u'*',
                                             'OPT': u'--',
                                             'OUT': u'*',
                                             'PKTS': u'0',
                                             'PROT': u'tcp',
                                             'SOURCE': u'0.0.0.0/0',
                                             'TARGET': u'MP_TRAFFIC_RATE_LIMIT'},
                                            {'REST': u'tcp dpt:6000'},
                                            {'BYTES': u'0',
                                             'DESTINATION': u'0.0.0.0/0',
                                             'IN': u'*',
                                             'OPT': u'--',
                                             'OUT': u'*',
                                             'PKTS': u'0',
                                             'PROT': u'tcp',
                                             'SOURCE': u'0.0.0.0/0',
                                             'TARGET': u'MP_TRAFFIC_RATE_LIMIT'},
                                            {'REST': u'multiport sports 8002,8003 ctstate RELATED,ESTABLISHED'},
                                            {'BYTES': u'0',
                                             'DESTINATION': u'0.0.0.0/0',
                                             'IN': u'*',
                                             'OPT': u'--',
                                             'OUT': u'*',
                                             'PKTS': u'0',
                                             'PROT': u'udp',
                                             'SOURCE': u'10.83.225.254',
                                             'TARGET': u'MP_TRAFFIC_RATE_LIMIT'},
                                            {'REST': u'udp spt:123 dpt:123'},
                                            {'BYTES': u'0',
                                             'DESTINATION': u'0.0.0.0/0',
                                             'IN': u'*',
                                             'OPT': u'--',
                                             'OUT': u'*',
                                             'PKTS': u'0',
                                             'PROT': u'tcp',
                                             'SOURCE': u'10.83.224.100',
                                             'TARGET': u'MP_TRAFFIC_RATE_LIMIT'},
                                            {'REST': u'tcp spt:8080'},
                                            {'BYTES': u'0',
                                             'DESTINATION': u'0.0.0.0/0',
                                             'IN': u'*',
                                             'OPT': u'--',
                                             'OUT': u'*',
                                             'PKTS': u'0',
                                             'PROT': u'tcp',
                                             'SOURCE': u'0.0.0.0/0',
                                             'TARGET': u'ACCEPT'},
                                            {'REST': u'tcp dpt:12000 state NEW'}],
                                  'REFERENCES': u'1'},
                  u'MP_TRAFFIC_RATE_LIMIT': {'CHAIN': [{'BYTES': u'15621',
                                                        'DESTINATION': u'0.0.0.0/0',
                                                        'IN': u'*',
                                                        'OPT': u'--',
                                                        'OUT': u'*',
                                                        'PKTS': u'254',
                                                        'PROT': u'all',
                                                        'SOURCE': u'0.0.0.0/0',
                                                        'TARGET': u'ACCEPT'},
                                                       {'REST': u'limit: avg 2000/sec burst 32'},
                                                       {'BYTES': u'0',
                                                        'DESTINATION': u'0.0.0.0/0',
                                                        'IN': u'*',
                                                        'OPT': u'--',
                                                        'OUT': u'*',
                                                        'PKTS': u'0',
                                                        'PROT': u'all',
                                                        'SOURCE': u'0.0.0.0/0',
                                                        'TARGET': u'DROP'}],
                                             'REFERENCES': u'15'},
                  u'OUTPUT': {'BYTES': u'87055714',
                              'CHAIN': [{'BYTES': u'18743328',
                                         'DESTINATION': u'0.0.0.0/0',
                                         'IN': u'*',
                                         'OPT': u'--',
                                         'OUT': u'*',
                                         'PKTS': u'38592',
                                         'PROT': u'icmp',
                                         'SOURCE': u'0.0.0.0/0',
                                         'TARGET': u'EGRESS_ICMP'}],
                              'PACKETS': u'50759',
                              'POLICY': u'ACCEPT'},
                  u'TLS_RENEG_RATE_LIMIT': {'CHAIN': [], 'REFERENCES': u'0'},
                  u'TOP_TRAFFIC_RATE_LIMIT': {'CHAIN': [], 'REFERENCES': u'0'},
                  u'UDP_ECHO_REQUEST_RATE_LIMIT': {'CHAIN': [{'BYTES': u'0',
                                                              'DESTINATION': u'0.0.0.0/0',
                                                              'IN': u'*',
                                                              'OPT': u'--',
                                                              'OUT': u'*',
                                                              'PKTS': u'0',
                                                              'PROT': u'all',
                                                              'SOURCE': u'0.0.0.0/0',
                                                              'TARGET': u'ACCEPT'},
                                                             {'REST': u'limit: avg 100/sec burst 5'},
                                                             {'BYTES': u'0',
                                                              'DESTINATION': u'0.0.0.0/0',
                                                              'IN': u'*',
                                                              'OPT': u'--',
                                                              'OUT': u'*',
                                                              'PKTS': u'0',
                                                              'PROT': u'all',
                                                              'SOURCE': u'0.0.0.0/0',
                                                              'TARGET': u'DROP'}],
                                                   'REFERENCES': u'1'}}
