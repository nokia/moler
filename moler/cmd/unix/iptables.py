# -*- coding: utf-8 -*-
"""
iptables command module.
"""

__author__ = 'Sylwester Golonka, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2021, Nokia'
__email__ = 'sylwester.golonka@nokia.com, marcin.usielski@nokia.com'

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
        self._key_details = list()

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
                self._parse_chain_policy(line)
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
            self._key_details = list()
            raise ParsingDone

    # Chain CP_TRAFFIC_RATE_LIMIT (1 references)
    _re_parse_chain_references = re.compile(r"Chain\s+(?P<NAME>\S+)\s+\((?P<REFERENCES>\d+) references\)$")

    def _parse_chain_references(self, line):
        if self._regex_helper.search_compiled(Iptables._re_parse_chain_references, line):
            self.chain = self._regex_helper.group("NAME")
            self.current_ret[self.chain] = dict()
            self.current_ret[self.chain]["REFERENCES"] = self._regex_helper.group("REFERENCES")
            self.current_ret[self.chain]["CHAIN"] = []
            self._key_details = list()
            raise ParsingDone

    # Chain INPUT (policy ACCEPT)
    _re_parse_chain_policy = re.compile(
        r"Chain\s+(?P<NAME>\S+)\s+\(policy\s(?P<POLICY>\S+)\)$")

    def _parse_chain_policy(self, line):
        if self._regex_helper.search_compiled(Iptables._re_parse_chain_policy, line):
            self.chain = self._regex_helper.group("NAME")
            self.current_ret[self.chain] = dict()
            self.current_ret[self.chain]["POLICY"] = self._regex_helper.group("POLICY")
            self.current_ret[self.chain]["CHAIN"] = []
            self._key_details = list()
            raise ParsingDone

    #    pkts      bytes target     prot opt in     out     source               destination
    _re_parse_headers = re.compile(r"(?P<HEADERS>pkts\s+bytes\s+target\s+prot\s+opt\s+in\s+out\s+source\s+destination)")

    def _parse_headers(self, line):
        if self.chain and 0 == len(self._key_details):
            matched = re.findall(r"\s*(\S+)\s*", line)
            if matched:
                for header in matched:
                    self._key_details.append(header.upper())
            raise ParsingDone

    #   0        0 ACCEPT     icmp --  *      *       0.0.0.0/0            0.0.0.0/0            icmptype 8 limit: avg 25/sec burst 5
    _re_parse_details = re.compile(r"(?P<VALUE>\S+)")

    def _parse_details(self, line):
        if self.chain and self._key_details and self._regex_helper.search_compiled(Iptables._re_parse_details, line):
            values = re.findall(Iptables._re_parse_details, line)
            ret = dict()
            if len(values) >= len(self._key_details):
                for value, key in zip(values, self._key_details):
                    ret[key] = value
                self.current_ret[self.chain]["CHAIN"].append(ret)
                re_for_rest = self._build_regex_for_rest()
                if self._regex_helper.search_compiled(re_for_rest, line):
                    ret = dict()
                    ret["REST"] = self._regex_helper.group("REST")
                    self.current_ret[self.chain]["CHAIN"][-1]['REST'] = ret['REST']
                    self.current_ret[self.chain]["CHAIN"].append(ret)  # For backward compatibility
                raise ParsingDone

    def _build_regex_for_rest(self):
        regex_for_rest = ""
        i = 0
        while i < len(self._key_details):
            regex_for_rest = r"{}\S+\s+".format(regex_for_rest)
            i += 1
        regex_for_rest = r"{}(?P<REST>\S.*\S|\S+)".format(regex_for_rest)
        re_for_rest = re.compile(regex_for_rest)
        return re_for_rest


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

COMMAND_RESULT = {'CP_TRAFFIC_RATE_LIMIT': {'CHAIN': [{'BYTES': '468',
                                                       'DESTINATION': '0.0.0.0/0',
                                                       'IN': '*',
                                                       'OPT': '--',
                                                       'OUT': '*',
                                                       'PKTS': '13',
                                                       'PROT': 'sctp',
                                                       'REST': 'limit: avg 2000/sec '
                                                               'burst 80',
                                                       'SOURCE': '0.0.0.0/0',
                                                       'TARGET': 'ACCEPT'},
                                                      {'REST': 'limit: avg 2000/sec '
                                                               'burst 80'},
                                                      {'BYTES': '0',
                                                       'DESTINATION': '0.0.0.0/0',
                                                       'IN': '*',
                                                       'OPT': '--',
                                                       'OUT': '*',
                                                       'PKTS': '0',
                                                       'PROT': 'sctp',
                                                       'SOURCE': '0.0.0.0/0',
                                                       'TARGET': 'DROP'}],
                                            'REFERENCES': '1'},
                  'DISCARD_CHAIN': {'CHAIN': [{'BYTES': '0',
                                               'DESTINATION': '0.0.0.0/0',
                                               'IN': '*',
                                               'OPT': '--',
                                               'OUT': '*',
                                               'PKTS': '0',
                                               'PROT': 'all',
                                               'SOURCE': '0.0.0.0/0',
                                               'TARGET': 'DROP'}],
                                    'REFERENCES': '2'},
                  'EGRESS_ICMP': {'CHAIN': [{'BYTES': '0',
                                             'DESTINATION': '0.0.0.0/0',
                                             'IN': '*',
                                             'OPT': '--',
                                             'OUT': '*',
                                             'PKTS': '0',
                                             'PROT': 'icmp',
                                             'REST': 'icmptype 8 ctstate '
                                                     'NEW,ESTABLISHED',
                                             'SOURCE': '0.0.0.0/0',
                                             'TARGET': 'EGRESS_ICMP_RATE_LIMIT'},
                                            {'REST': 'icmptype 8 ctstate '
                                                     'NEW,ESTABLISHED'},
                                            {'BYTES': '0',
                                             'DESTINATION': '0.0.0.0/0',
                                             'IN': '*',
                                             'OPT': '--',
                                             'OUT': '*',
                                             'PKTS': '0',
                                             'PROT': 'icmp',
                                             'REST': 'icmptype 0 ctstate '
                                                     'ESTABLISHED',
                                             'SOURCE': '0.0.0.0/0',
                                             'TARGET': 'EGRESS_ICMP_RATE_LIMIT'},
                                            {'REST': 'icmptype 0 ctstate ESTABLISHED'},
                                            {'BYTES': '18743328',
                                             'DESTINATION': '0.0.0.0/0',
                                             'IN': '*',
                                             'OPT': '--',
                                             'OUT': '*',
                                             'PKTS': '38592',
                                             'PROT': 'icmp',
                                             'REST': 'icmptype 3',
                                             'SOURCE': '0.0.0.0/0',
                                             'TARGET': 'EGRESS_ICMP_RATE_LIMIT'},
                                            {'REST': 'icmptype 3'},
                                            {'BYTES': '0',
                                             'DESTINATION': '0.0.0.0/0',
                                             'IN': '*',
                                             'OPT': '--',
                                             'OUT': '*',
                                             'PKTS': '0',
                                             'PROT': 'icmp',
                                             'REST': 'icmptype 11',
                                             'SOURCE': '0.0.0.0/0',
                                             'TARGET': 'EGRESS_ICMP_RATE_LIMIT'},
                                            {'REST': 'icmptype 11'},
                                            {'BYTES': '0',
                                             'DESTINATION': '0.0.0.0/0',
                                             'IN': '*',
                                             'OPT': '--',
                                             'OUT': '*',
                                             'PKTS': '0',
                                             'PROT': 'icmp',
                                             'REST': 'icmptype 12',
                                             'SOURCE': '0.0.0.0/0',
                                             'TARGET': 'ACCEPT'},
                                            {'REST': 'icmptype 12'},
                                            {'BYTES': '0',
                                             'DESTINATION': '0.0.0.0/0',
                                             'IN': '*',
                                             'OPT': '--',
                                             'OUT': '*',
                                             'PKTS': '0',
                                             'PROT': 'icmp',
                                             'SOURCE': '0.0.0.0/0',
                                             'TARGET': 'DISCARD_CHAIN'}],
                                  'REFERENCES': '1'},
                  'EGRESS_ICMP_RATE_LIMIT': {'CHAIN': [{'BYTES': '0',
                                                        'DESTINATION': '0.0.0.0/0',
                                                        'IN': '*',
                                                        'OPT': '--',
                                                        'OUT': '*',
                                                        'PKTS': '0',
                                                        'PROT': 'icmp',
                                                        'REST': 'icmptype 8 limit: '
                                                                'avg 25/sec burst 5',
                                                        'SOURCE': '0.0.0.0/0',
                                                        'TARGET': 'ACCEPT'},
                                                       {'REST': 'icmptype 8 limit: '
                                                                'avg 25/sec burst '
                                                                '5'},
                                                       {'BYTES': '0',
                                                        'DESTINATION': '0.0.0.0/0',
                                                        'IN': '*',
                                                        'OPT': '--',
                                                        'OUT': '*',
                                                        'PKTS': '0',
                                                        'PROT': 'icmp',
                                                        'REST': 'icmptype 0 limit: '
                                                                'avg 25/sec burst 5',
                                                        'SOURCE': '0.0.0.0/0',
                                                        'TARGET': 'ACCEPT'},
                                                       {'REST': 'icmptype 0 limit: '
                                                                'avg 25/sec burst '
                                                                '5'},
                                                       {'BYTES': '2834715',
                                                        'DESTINATION': '0.0.0.0/0',
                                                        'IN': '*',
                                                        'OPT': '--',
                                                        'OUT': '*',
                                                        'PKTS': '6101',
                                                        'PROT': 'icmp',
                                                        'REST': 'icmptype 3 limit: '
                                                                'avg 25/sec burst 5',
                                                        'SOURCE': '0.0.0.0/0',
                                                        'TARGET': 'ACCEPT'},
                                                       {'REST': 'icmptype 3 limit: '
                                                                'avg 25/sec burst '
                                                                '5'},
                                                       {'BYTES': '0',
                                                        'DESTINATION': '0.0.0.0/0',
                                                        'IN': '*',
                                                        'OPT': '--',
                                                        'OUT': '*',
                                                        'PKTS': '0',
                                                        'PROT': 'icmp',
                                                        'REST': 'icmptype 11 limit: '
                                                                'avg 25/sec burst 5',
                                                        'SOURCE': '0.0.0.0/0',
                                                        'TARGET': 'ACCEPT'},
                                                       {'REST': 'icmptype 11 limit: '
                                                                'avg 25/sec burst '
                                                                '5'},
                                                       {'BYTES': '15908613',
                                                        'DESTINATION': '0.0.0.0/0',
                                                        'IN': '*',
                                                        'OPT': '--',
                                                        'OUT': '*',
                                                        'PKTS': '32491',
                                                        'PROT': 'icmp',
                                                        'SOURCE': '0.0.0.0/0',
                                                        'TARGET': 'DROP'}],
                                             'REFERENCES': '4'},
                  'FORWARD': {'BYTES': '0',
                              'CHAIN': [{'BYTES': '0',
                                         'DESTINATION': '0.0.0.0/0',
                                         'IN': '*',
                                         'OPT': '--',
                                         'OUT': '*',
                                         'PKTS': '0',
                                         'PROT': 'udp',
                                         'REST': 'multiport sports '
                                                 '13080:13099,13120:13140',
                                         'SOURCE': '10.1.52.248',
                                         'TARGET': 'MP_TRAFFIC_RATE_LIMIT'},
                                        {'REST': 'multiport sports '
                                                 '13080:13099,13120:13140'},
                                        {'BYTES': '0',
                                         'DESTINATION': '0.0.0.0/0',
                                         'IN': '*',
                                         'OPT': '--',
                                         'OUT': '*',
                                         'PKTS': '0',
                                         'PROT': 'tcp',
                                         'REST': 'multiport sports '
                                                 '15008,15010:15029',
                                         'SOURCE': '10.1.52.248',
                                         'TARGET': 'MP_TRAFFIC_RATE_LIMIT'},
                                        {'REST': 'multiport sports 15008,15010:15029'}],
                              'PACKETS': '0',
                              'POLICY': 'DROP'},
                  'INGRESS_ICMP': {'CHAIN': [{'BYTES': '0',
                                              'DESTINATION': '0.0.0.0/0',
                                              'IN': '*',
                                              'OPT': '--',
                                              'OUT': '*',
                                              'PKTS': '0',
                                              'PROT': 'icmp',
                                              'REST': 'icmptype 8 ctstate '
                                                      'NEW,ESTABLISHED',
                                              'SOURCE': '0.0.0.0/0',
                                              'TARGET': 'INGRESS_ICMP_RATE_LIMIT'},
                                             {'REST': 'icmptype 8 ctstate '
                                                      'NEW,ESTABLISHED'},
                                             {'BYTES': '0',
                                              'DESTINATION': '0.0.0.0/0',
                                              'IN': '*',
                                              'OPT': '--',
                                              'OUT': '*',
                                              'PKTS': '0',
                                              'PROT': 'icmp',
                                              'REST': 'icmptype 0 ctstate '
                                                      'ESTABLISHED',
                                              'SOURCE': '0.0.0.0/0',
                                              'TARGET': 'INGRESS_ICMP_RATE_LIMIT'},
                                             {'REST': 'icmptype 0 ctstate ESTABLISHED'},
                                             {'BYTES': '0',
                                              'DESTINATION': '0.0.0.0/0',
                                              'IN': '*',
                                              'OPT': '--',
                                              'OUT': '*',
                                              'PKTS': '0',
                                              'PROT': 'icmp',
                                              'REST': 'icmptype 3',
                                              'SOURCE': '0.0.0.0/0',
                                              'TARGET': 'ACCEPT'},
                                             {'REST': 'icmptype 3'},
                                             {'BYTES': '0',
                                              'DESTINATION': '0.0.0.0/0',
                                              'IN': '*',
                                              'OPT': '--',
                                              'OUT': '*',
                                              'PKTS': '0',
                                              'PROT': 'icmp',
                                              'REST': 'icmptype 11',
                                              'SOURCE': '0.0.0.0/0',
                                              'TARGET': 'ACCEPT'},
                                             {'REST': 'icmptype 11'},
                                             {'BYTES': '0',
                                              'DESTINATION': '0.0.0.0/0',
                                              'IN': '*',
                                              'OPT': '--',
                                              'OUT': '*',
                                              'PKTS': '0',
                                              'PROT': 'icmp',
                                              'REST': 'icmptype 12',
                                              'SOURCE': '0.0.0.0/0',
                                              'TARGET': 'ACCEPT'},
                                             {'REST': 'icmptype 12'},
                                             {'BYTES': '0',
                                              'DESTINATION': '0.0.0.0/0',
                                              'IN': '*',
                                              'OPT': '--',
                                              'OUT': '*',
                                              'PKTS': '0',
                                              'PROT': 'icmp',
                                              'SOURCE': '0.0.0.0/0',
                                              'TARGET': 'DISCARD_CHAIN'}],
                                   'REFERENCES': '1'},
                  'INGRESS_ICMP_RATE_LIMIT': {'CHAIN': [{'BYTES': '0',
                                                         'DESTINATION': '0.0.0.0/0',
                                                         'IN': '*',
                                                         'OPT': '--',
                                                         'OUT': '*',
                                                         'PKTS': '0',
                                                         'PROT': 'icmp',
                                                         'REST': 'icmptype 8 limit: '
                                                                 'avg 25/sec burst '
                                                                 '8',
                                                         'SOURCE': '0.0.0.0/0',
                                                         'TARGET': 'ACCEPT'},
                                                        {'REST': 'icmptype 8 limit: '
                                                                 'avg 25/sec burst '
                                                                 '8'},
                                                        {'BYTES': '0',
                                                         'DESTINATION': '0.0.0.0/0',
                                                         'IN': '*',
                                                         'OPT': '--',
                                                         'OUT': '*',
                                                         'PKTS': '0',
                                                         'PROT': 'icmp',
                                                         'REST': 'icmptype 0 limit: '
                                                                 'avg 25/sec burst '
                                                                 '8',
                                                         'SOURCE': '0.0.0.0/0',
                                                         'TARGET': 'ACCEPT'},
                                                        {'REST': 'icmptype 0 limit: '
                                                                 'avg 25/sec burst '
                                                                 '8'},
                                                        {'BYTES': '0',
                                                         'DESTINATION': '0.0.0.0/0',
                                                         'IN': '*',
                                                         'OPT': '--',
                                                         'OUT': '*',
                                                         'PKTS': '0',
                                                         'PROT': 'icmp',
                                                         'SOURCE': '0.0.0.0/0',
                                                         'TARGET': 'DROP'}],
                                              'REFERENCES': '2'},
                  'INPUT': {'BYTES': '3054',
                            'CHAIN': [{'BYTES': '0',
                                       'DESTINATION': '0.0.0.0/0',
                                       'IN': '*',
                                       'OPT': '--',
                                       'OUT': '*',
                                       'PKTS': '0',
                                       'PROT': 'all',
                                       'REST': 'u32 '
                                               '"0x0&0xf000000=0x6000000:0xf000000"',
                                       'SOURCE': '0.0.0.0/0',
                                       'TARGET': 'DROP'},
                                      {'REST': 'u32 '
                                               '"0x0&0xf000000=0x6000000:0xf000000"'},
                                      {'BYTES': '0',
                                       'DESTINATION': '0.0.0.0/0',
                                       'IN': 'br0+',
                                       'OPT': '--',
                                       'OUT': '*',
                                       'PKTS': '0',
                                       'PROT': 'tcp',
                                       'REST': 'multiport dports 15010:15014 state '
                                               'RELATED,ESTABLISHED',
                                       'SOURCE': '0.0.0.0/0',
                                       'TARGET': 'ACCEPT'},
                                      {'REST': 'multiport dports 15010:15014 state '
                                               'RELATED,ESTABLISHED'},
                                      {'BYTES': '0',
                                       'DESTINATION': '0.0.0.0/0',
                                       'IN': 'eth4',
                                       'OPT': '--',
                                       'OUT': '*',
                                       'PKTS': '0',
                                       'PROT': 'all',
                                       'SOURCE': '0.0.0.0/0',
                                       'TARGET': 'ACCEPT'},
                                      {'BYTES': '0',
                                       'DESTINATION': '0.0.0.0/0',
                                       'IN': '*',
                                       'OPT': '--',
                                       'OUT': '*',
                                       'PKTS': '0',
                                       'PROT': 'udp',
                                       'REST': 'udp dpt:16009',
                                       'SOURCE': '0.0.0.0/0',
                                       'TARGET': 'ACCEPT'},
                                      {'REST': 'udp dpt:16009'},
                                      {'BYTES': '0',
                                       'DESTINATION': '0.0.0.0/0',
                                       'IN': '*',
                                       'OPT': '--',
                                       'OUT': '*',
                                       'PKTS': '0',
                                       'PROT': 'esp',
                                       'SOURCE': '0.0.0.0/0',
                                       'TARGET': 'ACCEPT'},
                                      {'BYTES': '52497455',
                                       'DESTINATION': '0.0.0.0/0',
                                       'IN': 'lo',
                                       'OPT': '--',
                                       'OUT': '*',
                                       'PKTS': '17207',
                                       'PROT': 'all',
                                       'SOURCE': '0.0.0.0/0',
                                       'TARGET': 'ACCEPT'},
                                      {'BYTES': '0',
                                       'DESTINATION': '0.0.0.0/0',
                                       'IN': '*',
                                       'OPT': '--',
                                       'OUT': '*',
                                       'PKTS': '0',
                                       'PROT': 'udp',
                                       'REST': 'udp spt:67 dpt:68 ctstate '
                                               'RELATED,ESTABLISHED',
                                       'SOURCE': '0.0.0.0/0',
                                       'TARGET': 'ACCEPT'},
                                      {'REST': 'udp spt:67 dpt:68 ctstate '
                                               'RELATED,ESTABLISHED'},
                                      {'BYTES': '0',
                                       'DESTINATION': '0.0.0.0/0',
                                       'IN': '*',
                                       'OPT': '--',
                                       'OUT': '*',
                                       'PKTS': '0',
                                       'PROT': 'all',
                                       'REST': 'u32 "0x0&0xf000000>>0x18=0x6:0xf"',
                                       'SOURCE': '0.0.0.0/0',
                                       'TARGET': 'DROP'},
                                      {'REST': 'u32 "0x0&0xf000000>>0x18=0x6:0xf"'},
                                      {'BYTES': '0',
                                       'DESTINATION': '0.0.0.0/0',
                                       'IN': '*',
                                       'OPT': '--',
                                       'OUT': '*',
                                       'PKTS': '0',
                                       'PROT': 'all',
                                       'REST': 'u32 "0x0&0xffff=0x3fe1:0xffff"',
                                       'SOURCE': '0.0.0.0/0',
                                       'TARGET': 'DROP'},
                                      {'REST': 'u32 "0x0&0xffff=0x3fe1:0xffff"'},
                                      {'BYTES': '0',
                                       'DESTINATION': '0.0.0.0/0',
                                       'IN': '*',
                                       'OPT': '--',
                                       'OUT': '*',
                                       'PKTS': '0',
                                       'PROT': 'tcp',
                                       'REST': 'tcp dpt:21',
                                       'SOURCE': '0.0.0.0/0',
                                       'TARGET': 'DROP'},
                                      {'REST': 'tcp dpt:21'},
                                      {'BYTES': '3054',
                                       'DESTINATION': '0.0.0.0/0',
                                       'IN': 'eth1+',
                                       'OPT': '--',
                                       'OUT': '*',
                                       'PKTS': '12',
                                       'PROT': 'all',
                                       'SOURCE': '192.168.255.0/24',
                                       'TARGET': 'ACCEPT'},
                                      {'BYTES': '0',
                                       'DESTINATION': '0.0.0.0/0',
                                       'IN': '*',
                                       'OPT': '--',
                                       'OUT': '*',
                                       'PKTS': '0',
                                       'PROT': 'udp',
                                       'REST': 'udp dpts:5001:5010 ctstate '
                                               'RELATED,ESTABLISHED',
                                       'SOURCE': '0.0.0.0/0',
                                       'TARGET': 'ACCEPT'},
                                      {'REST': 'udp dpts:5001:5010 ctstate '
                                               'RELATED,ESTABLISHED'},
                                      {'BYTES': '0',
                                       'DESTINATION': '0.0.0.0/0',
                                       'IN': '*',
                                       'OPT': '--',
                                       'OUT': '*',
                                       'PKTS': '0',
                                       'PROT': 'udp',
                                       'REST': 'udp spts:5001:5010',
                                       'SOURCE': '0.0.0.0/0',
                                       'TARGET': 'UDP_ECHO_REQUEST_RATE_LIMIT'},
                                      {'REST': 'udp spts:5001:5010'},
                                      {'BYTES': '0',
                                       'DESTINATION': '0.0.0.0/0',
                                       'IN': '*',
                                       'OPT': '--',
                                       'OUT': '*',
                                       'PKTS': '0',
                                       'PROT': 'udp',
                                       'REST': 'udp spt:7 dpt:7',
                                       'SOURCE': '0.0.0.0/0',
                                       'TARGET': 'DROP'},
                                      {'REST': 'udp spt:7 dpt:7'},
                                      {'BYTES': '0',
                                       'DESTINATION': '0.0.0.0/0',
                                       'IN': '*',
                                       'OPT': '--',
                                       'OUT': '*',
                                       'PKTS': '0',
                                       'PROT': 'udp',
                                       'REST': 'udp dpts:33434:33933 ADDRTYPE match '
                                               'dst-type LOCAL',
                                       'SOURCE': '0.0.0.0/0',
                                       'TARGET': 'ACCEPT'},
                                      {'REST': 'udp dpts:33434:33933 ADDRTYPE match '
                                               'dst-type LOCAL'},
                                      {'BYTES': '0',
                                       'DESTINATION': '0.0.0.0/0',
                                       'IN': 'br0+',
                                       'OPT': '--',
                                       'OUT': '*',
                                       'PKTS': '0',
                                       'PROT': 'icmp',
                                       'SOURCE': '0.0.0.0/0',
                                       'TARGET': 'INGRESS_ICMP'},
                                      {'BYTES': '0',
                                       'DESTINATION': '10.0.0.248',
                                       'IN': 'br0+',
                                       'OPT': '--',
                                       'OUT': '*',
                                       'PKTS': '0',
                                       'PROT': 'udp',
                                       'REST': 'udp dpt:2152',
                                       'SOURCE': '0.0.0.0/0',
                                       'TARGET': 'ACCEPT'},
                                      {'REST': 'udp dpt:2152'},
                                      {'BYTES': '0',
                                       'DESTINATION': '10.0.111.248',
                                       'IN': 'br0+',
                                       'OPT': '--',
                                       'OUT': '*',
                                       'PKTS': '0',
                                       'PROT': 'udp',
                                       'REST': 'udp dpt:2152',
                                       'SOURCE': '0.0.0.0/0',
                                       'TARGET': 'ACCEPT'},
                                      {'REST': 'udp dpt:2152'},
                                      {'BYTES': '468',
                                       'DESTINATION': '10.0.0.248',
                                       'IN': 'br0+',
                                       'OPT': '--',
                                       'OUT': '*',
                                       'PKTS': '13',
                                       'PROT': 'sctp',
                                       'SOURCE': '0.0.0.0/0',
                                       'TARGET': 'CP_TRAFFIC_RATE_LIMIT'},
                                      {'BYTES': '0',
                                       'DESTINATION': '10.0.0.248',
                                       'IN': '*',
                                       'OPT': '--',
                                       'OUT': '*',
                                       'PKTS': '0',
                                       'PROT': 'udp',
                                       'REST': 'udp dpt:500',
                                       'SOURCE': '0.0.0.0/0',
                                       'TARGET': 'ACCEPT'},
                                      {'REST': 'udp dpt:500'},
                                      {'BYTES': '0',
                                       'DESTINATION': '10.0.111.248',
                                       'IN': '*',
                                       'OPT': '--',
                                       'OUT': '*',
                                       'PKTS': '0',
                                       'PROT': 'udp',
                                       'REST': 'udp dpt:500',
                                       'SOURCE': '0.0.0.0/0',
                                       'TARGET': 'ACCEPT'},
                                      {'REST': 'udp dpt:500'},
                                      {'BYTES': '15621',
                                       'DESTINATION': '10.1.52.248',
                                       'IN': '*',
                                       'OPT': '--',
                                       'OUT': '*',
                                       'PKTS': '254',
                                       'PROT': 'all',
                                       'SOURCE': '0.0.0.0/0',
                                       'TARGET': 'MP_TRAFFIC'},
                                      {'BYTES': '0',
                                       'DESTINATION': '0.0.0.0/0',
                                       'IN': '*',
                                       'OPT': '--',
                                       'OUT': '*',
                                       'PKTS': '0',
                                       'PROT': 'tcp',
                                       'REST': 'tcp spt:389 ctstate '
                                               'RELATED,ESTABLISHED',
                                       'SOURCE': '10.83.225.1',
                                       'TARGET': 'MP_TRAFFIC_RATE_LIMIT'},
                                      {'REST': 'tcp spt:389 ctstate '
                                               'RELATED,ESTABLISHED'},
                                      {'BYTES': '0',
                                       'DESTINATION': '0.0.0.0/0',
                                       'IN': '*',
                                       'OPT': '--',
                                       'OUT': '*',
                                       'PKTS': '0',
                                       'PROT': 'tcp',
                                       'REST': 'multiport dports 15001:15005,15007',
                                       'SOURCE': '0.0.0.0/0',
                                       'TARGET': 'ACCEPT'},
                                      {'REST': 'multiport dports 15001:15005,15007'},
                                      {'BYTES': '0',
                                       'DESTINATION': '0.0.0.0/0',
                                       'IN': '*',
                                       'OPT': '--',
                                       'OUT': '*',
                                       'PKTS': '0',
                                       'PROT': 'tcp',
                                       'REST': 'tcp dpt:22',
                                       'SOURCE': '0.0.0.0/0',
                                       'TARGET': 'ACCEPT'},
                                      {'REST': 'tcp dpt:22'}],
                            'PACKETS': '12',
                            'POLICY': 'DROP'},
                  'MP_TRAFFIC': {'CHAIN': [{'BYTES': '0',
                                            'DESTINATION': '0.0.0.0/0',
                                            'IN': '*',
                                            'OPT': '--',
                                            'OUT': '*',
                                            'PKTS': '0',
                                            'PROT': 'udp',
                                            'REST': 'udp spt:53 ctstate '
                                                    'RELATED,ESTABLISHED',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'MP_TRAFFIC_RATE_LIMIT'},
                                           {'REST': 'udp spt:53 ctstate '
                                                    'RELATED,ESTABLISHED'},
                                           {'BYTES': '0',
                                            'DESTINATION': '0.0.0.0/0',
                                            'IN': '*',
                                            'OPT': '--',
                                            'OUT': '*',
                                            'PKTS': '0',
                                            'PROT': 'tcp',
                                            'REST': 'tcp spt:53 ctstate '
                                                    'RELATED,ESTABLISHED',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'MP_TRAFFIC_RATE_LIMIT'},
                                           {'REST': 'tcp spt:53 ctstate '
                                                    'RELATED,ESTABLISHED'},
                                           {'BYTES': '0',
                                            'DESTINATION': '0.0.0.0/0',
                                            'IN': '*',
                                            'OPT': '--',
                                            'OUT': '*',
                                            'PKTS': '0',
                                            'PROT': 'tcp',
                                            'REST': 'tcp spt:21 ctstate '
                                                    'RELATED,ESTABLISHED',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'MP_TRAFFIC_RATE_LIMIT'},
                                           {'REST': 'tcp spt:21 ctstate '
                                                    'RELATED,ESTABLISHED'},
                                           {'BYTES': '0',
                                            'DESTINATION': '0.0.0.0/0',
                                            'IN': '*',
                                            'OPT': '--',
                                            'OUT': '*',
                                            'PKTS': '0',
                                            'PROT': 'tcp',
                                            'REST': 'tcp spt:20 dpts:1024:65535 '
                                                    'ctstate RELATED,ESTABLISHED',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'MP_TRAFFIC_RATE_LIMIT'},
                                           {'REST': 'tcp spt:20 dpts:1024:65535 '
                                                    'ctstate RELATED,ESTABLISHED'},
                                           {'BYTES': '0',
                                            'DESTINATION': '0.0.0.0/0',
                                            'IN': '*',
                                            'OPT': '--',
                                            'OUT': '*',
                                            'PKTS': '0',
                                            'PROT': 'tcp',
                                            'REST': 'tcp spt:22 dpts:1024:65535 '
                                                    'ctstate RELATED,ESTABLISHED',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'MP_TRAFFIC_RATE_LIMIT'},
                                           {'REST': 'tcp spt:22 dpts:1024:65535 '
                                                    'ctstate RELATED,ESTABLISHED'},
                                           {'BYTES': '0',
                                            'DESTINATION': '0.0.0.0/0',
                                            'IN': '*',
                                            'OPT': '--',
                                            'OUT': '*',
                                            'PKTS': '0',
                                            'PROT': 'tcp',
                                            'REST': 'tcp spt:23 dpts:1024:65535 '
                                                    'ctstate RELATED,ESTABLISHED',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'MP_TRAFFIC_RATE_LIMIT'},
                                           {'REST': 'tcp spt:23 dpts:1024:65535 '
                                                    'ctstate RELATED,ESTABLISHED'},
                                           {'BYTES': '15621',
                                            'DESTINATION': '0.0.0.0/0',
                                            'IN': '*',
                                            'OPT': '--',
                                            'OUT': '*',
                                            'PKTS': '254',
                                            'PROT': 'tcp',
                                            'REST': 'ctstate RELATED,ESTABLISHED',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'MP_TRAFFIC_RATE_LIMIT'},
                                           {'REST': 'ctstate RELATED,ESTABLISHED'},
                                           {'BYTES': '0',
                                            'DESTINATION': '0.0.0.0/0',
                                            'IN': '*',
                                            'OPT': '--',
                                            'OUT': '*',
                                            'PKTS': '0',
                                            'PROT': 'tcp',
                                            'REST': 'multiport dports 6001,443',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'MP_TRAFFIC_RATE_LIMIT'},
                                           {'REST': 'multiport dports 6001,443'},
                                           {'BYTES': '0',
                                            'DESTINATION': '0.0.0.0/0',
                                            'IN': '*',
                                            'OPT': '--',
                                            'OUT': '*',
                                            'PKTS': '0',
                                            'PROT': 'tcp',
                                            'REST': 'tcp dpt:6000',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'MP_TRAFFIC_RATE_LIMIT'},
                                           {'REST': 'tcp dpt:6000'},
                                           {'BYTES': '0',
                                            'DESTINATION': '0.0.0.0/0',
                                            'IN': '*',
                                            'OPT': '--',
                                            'OUT': '*',
                                            'PKTS': '0',
                                            'PROT': 'tcp',
                                            'REST': 'multiport sports 8002,8003 '
                                                    'ctstate RELATED,ESTABLISHED',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'MP_TRAFFIC_RATE_LIMIT'},
                                           {'REST': 'multiport sports 8002,8003 '
                                                    'ctstate RELATED,ESTABLISHED'},
                                           {'BYTES': '0',
                                            'DESTINATION': '0.0.0.0/0',
                                            'IN': '*',
                                            'OPT': '--',
                                            'OUT': '*',
                                            'PKTS': '0',
                                            'PROT': 'udp',
                                            'REST': 'udp spt:123 dpt:123',
                                            'SOURCE': '10.83.225.254',
                                            'TARGET': 'MP_TRAFFIC_RATE_LIMIT'},
                                           {'REST': 'udp spt:123 dpt:123'},
                                           {'BYTES': '0',
                                            'DESTINATION': '0.0.0.0/0',
                                            'IN': '*',
                                            'OPT': '--',
                                            'OUT': '*',
                                            'PKTS': '0',
                                            'PROT': 'tcp',
                                            'REST': 'tcp spt:8080',
                                            'SOURCE': '10.83.224.100',
                                            'TARGET': 'MP_TRAFFIC_RATE_LIMIT'},
                                           {'REST': 'tcp spt:8080'},
                                           {'BYTES': '0',
                                            'DESTINATION': '0.0.0.0/0',
                                            'IN': '*',
                                            'OPT': '--',
                                            'OUT': '*',
                                            'PKTS': '0',
                                            'PROT': 'tcp',
                                            'REST': 'tcp dpt:12000 state NEW',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'ACCEPT'},
                                           {'REST': 'tcp dpt:12000 state NEW'}],
                                 'REFERENCES': '1'},
                  'MP_TRAFFIC_RATE_LIMIT': {'CHAIN': [{'BYTES': '15621',
                                                       'DESTINATION': '0.0.0.0/0',
                                                       'IN': '*',
                                                       'OPT': '--',
                                                       'OUT': '*',
                                                       'PKTS': '254',
                                                       'PROT': 'all',
                                                       'REST': 'limit: avg 2000/sec '
                                                               'burst 32',
                                                       'SOURCE': '0.0.0.0/0',
                                                       'TARGET': 'ACCEPT'},
                                                      {'REST': 'limit: avg 2000/sec '
                                                               'burst 32'},
                                                      {'BYTES': '0',
                                                       'DESTINATION': '0.0.0.0/0',
                                                       'IN': '*',
                                                       'OPT': '--',
                                                       'OUT': '*',
                                                       'PKTS': '0',
                                                       'PROT': 'all',
                                                       'SOURCE': '0.0.0.0/0',
                                                       'TARGET': 'DROP'}],
                                            'REFERENCES': '15'},
                  'OUTPUT': {'BYTES': '87055714',
                             'CHAIN': [{'BYTES': '18743328',
                                        'DESTINATION': '0.0.0.0/0',
                                        'IN': '*',
                                        'OPT': '--',
                                        'OUT': '*',
                                        'PKTS': '38592',
                                        'PROT': 'icmp',
                                        'SOURCE': '0.0.0.0/0',
                                        'TARGET': 'EGRESS_ICMP'}],
                             'PACKETS': '50759',
                             'POLICY': 'ACCEPT'},
                  'TLS_RENEG_RATE_LIMIT': {'CHAIN': [], 'REFERENCES': '0'},
                  'TOP_TRAFFIC_RATE_LIMIT': {'CHAIN': [], 'REFERENCES': '0'},
                  'UDP_ECHO_REQUEST_RATE_LIMIT': {'CHAIN': [{'BYTES': '0',
                                                             'DESTINATION': '0.0.0.0/0',
                                                             'IN': '*',
                                                             'OPT': '--',
                                                             'OUT': '*',
                                                             'PKTS': '0',
                                                             'PROT': 'all',
                                                             'REST': 'limit: avg '
                                                                     '100/sec burst '
                                                                     '5',
                                                             'SOURCE': '0.0.0.0/0',
                                                             'TARGET': 'ACCEPT'},
                                                            {'REST': 'limit: avg '
                                                                     '100/sec burst '
                                                                     '5'},
                                                            {'BYTES': '0',
                                                             'DESTINATION': '0.0.0.0/0',
                                                             'IN': '*',
                                                             'OPT': '--',
                                                             'OUT': '*',
                                                             'PKTS': '0',
                                                             'PROT': 'all',
                                                             'SOURCE': '0.0.0.0/0',
                                                             'TARGET': 'DROP'}],
                                                  'REFERENCES': '1'}}

COMMAND_OUTPUT_frm2 = """
iptables -L INPUT -t mangle -n
Chain INPUT (policy ACCEPT)
target     prot opt source               destination
ACCEPT     all  --  0.0.0.0/0            0.0.0.0/0
ACCEPT     all  --  0.0.0.0/0            0.0.0.0/0
ACCEPT     all  --  0.0.0.0/0            0.0.0.0/0
ACCEPT     all  --  0.0.0.0/0            0.0.0.0/0
DROP       all  --  192.168.11.0/24      0.0.0.0/0
DROP       all  --  0.0.0.0/0            192.168.11.0/24
DROP       all  --  192.168.13.0/24      0.0.0.0/0
DROP       all  --  0.0.0.0/0            192.168.13.0/24
DROP       all  --  127.0.0.1            0.0.0.0/0
DROP       all  --  0.0.0.0/0            127.0.0.1
DROP       all  --  192.168.11.0/24      0.0.0.0/0
DROP       all  --  0.0.0.0/0            192.168.11.0/24
DROP       all  --  192.168.13.0/24      0.0.0.0/0
DROP       all  --  0.0.0.0/0            192.168.13.0/24
DROP       all  --  127.0.0.1            0.0.0.0/0
DROP       all  --  0.0.0.0/0            127.0.0.1
ACCEPT     tcp  --  0.0.0.0/0            10.83.182.143        tcp dpt:8080 state NEW limit: up to 100/min burst 10
DROP       tcp  --  0.0.0.0/0            10.83.182.143        tcp dpt:8080 state NEW
ACCEPT     tcp  --  0.0.0.0/0            10.83.182.143        tcp dpt:8443 state NEW limit: up to 100/min burst 10
DROP       tcp  --  0.0.0.0/0            10.83.182.143        tcp dpt:8443 state NEW
ACCEPT     udp  --  10.56.126.31         10.83.182.143        udp spt:53 state ESTABLISHED
ACCEPT     tcp  --  10.56.126.31         10.83.182.143        tcp spt:53 state ESTABLISHED
ACCEPT     udp  --  10.83.200.2          10.83.182.143        udp spt:123 dpt:123
ACCEPT     udp  --  10.83.200.3          10.83.182.143        udp spt:123 dpt:123
ACCEPT     udp  --  10.83.200.4          10.83.182.143        udp spt:123 dpt:123
ACCEPT     udp  --  0.0.0.0/0            0.0.0.0/0            udp dpts:33434:33933 limit: avg 25/sec burst 10
DROP       udp  --  0.0.0.0/0            0.0.0.0/0            udp dpts:33434:33933
ACCEPT     icmp --  0.0.0.0/0            0.0.0.0/0            icmptype 8 limit: avg 25/sec burst 8
DROP       icmp --  0.0.0.0/0            0.0.0.0/0            icmptype 8
ACCEPT     icmp --  0.0.0.0/0            0.0.0.0/0            icmptype 0 limit: avg 25/sec burst 8
DROP       icmp --  0.0.0.0/0            0.0.0.0/0            icmptype 0
ACCEPT     icmp --  0.0.0.0/0            0.0.0.0/0            icmptype 3 limit: avg 25/sec burst 8
DROP       icmp --  0.0.0.0/0            0.0.0.0/0            icmptype 3
ACCEPT     icmp --  0.0.0.0/0            0.0.0.0/0            icmptype 11 limit: avg 25/sec burst 8
DROP       icmp --  0.0.0.0/0            0.0.0.0/0            icmptype 11
ACCEPT     tcp  --  0.0.0.0/0            10.83.182.143        tcp dpt:22 state NEW limit: up to 5/sec burst 10 mode srcip htable-expire 60000
DROP       tcp  --  0.0.0.0/0            10.83.182.143        tcp dpt:22 state NEW
ACCEPT     tcp  --  0.0.0.0/0            10.83.182.143        tcp dpt:443 state NEW limit: up to 5/sec burst 10 mode srcip htable-expire 60000
DROP       tcp  --  0.0.0.0/0            10.83.182.143        tcp dpt:443 state NEW
ACCEPT     tcp  --  0.0.0.0/0            0.0.0.0/0            state RELATED,ESTABLISHED
DROP       all  --  0.0.0.0/0            0.0.0.0/0
host# $"""

COMMAND_KWARGS_frm2 = {
    'options': '-L INPUT -t mangle -n'
}

COMMAND_RESULT_frm2 = {'INPUT': {'CHAIN': [{'DESTINATION': '0.0.0.0/0',
                                            'OPT': '--',
                                            'PROT': 'all',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'ACCEPT'},
                                           {'DESTINATION': '0.0.0.0/0',
                                            'OPT': '--',
                                            'PROT': 'all',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'ACCEPT'},
                                           {'DESTINATION': '0.0.0.0/0',
                                            'OPT': '--',
                                            'PROT': 'all',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'ACCEPT'},
                                           {'DESTINATION': '0.0.0.0/0',
                                            'OPT': '--',
                                            'PROT': 'all',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'ACCEPT'},
                                           {'DESTINATION': '0.0.0.0/0',
                                            'OPT': '--',
                                            'PROT': 'all',
                                            'SOURCE': '192.168.11.0/24',
                                            'TARGET': 'DROP'},
                                           {'DESTINATION': '192.168.11.0/24',
                                            'OPT': '--',
                                            'PROT': 'all',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'DROP'},
                                           {'DESTINATION': '0.0.0.0/0',
                                            'OPT': '--',
                                            'PROT': 'all',
                                            'SOURCE': '192.168.13.0/24',
                                            'TARGET': 'DROP'},
                                           {'DESTINATION': '192.168.13.0/24',
                                            'OPT': '--',
                                            'PROT': 'all',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'DROP'},
                                           {'DESTINATION': '0.0.0.0/0',
                                            'OPT': '--',
                                            'PROT': 'all',
                                            'SOURCE': '127.0.0.1',
                                            'TARGET': 'DROP'},
                                           {'DESTINATION': '127.0.0.1',
                                            'OPT': '--',
                                            'PROT': 'all',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'DROP'},
                                           {'DESTINATION': '0.0.0.0/0',
                                            'OPT': '--',
                                            'PROT': 'all',
                                            'SOURCE': '192.168.11.0/24',
                                            'TARGET': 'DROP'},
                                           {'DESTINATION': '192.168.11.0/24',
                                            'OPT': '--',
                                            'PROT': 'all',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'DROP'},
                                           {'DESTINATION': '0.0.0.0/0',
                                            'OPT': '--',
                                            'PROT': 'all',
                                            'SOURCE': '192.168.13.0/24',
                                            'TARGET': 'DROP'},
                                           {'DESTINATION': '192.168.13.0/24',
                                            'OPT': '--',
                                            'PROT': 'all',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'DROP'},
                                           {'DESTINATION': '0.0.0.0/0',
                                            'OPT': '--',
                                            'PROT': 'all',
                                            'SOURCE': '127.0.0.1',
                                            'TARGET': 'DROP'},
                                           {'DESTINATION': '127.0.0.1',
                                            'OPT': '--',
                                            'PROT': 'all',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'DROP'},
                                           {'DESTINATION': '10.83.182.143',
                                            'OPT': '--',
                                            'PROT': 'tcp',
                                            'REST': 'tcp dpt:8080 state NEW limit: up to '
                                                    '100/min burst 10',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'ACCEPT'},
                                           {'REST': 'tcp dpt:8080 state NEW limit: up to '
                                                    '100/min burst 10'},
                                           {'DESTINATION': '10.83.182.143',
                                            'OPT': '--',
                                            'PROT': 'tcp',
                                            'REST': 'tcp dpt:8080 state NEW',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'DROP'},
                                           {'REST': 'tcp dpt:8080 state NEW'},
                                           {'DESTINATION': '10.83.182.143',
                                            'OPT': '--',
                                            'PROT': 'tcp',
                                            'REST': 'tcp dpt:8443 state NEW limit: up to '
                                                    '100/min burst 10',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'ACCEPT'},
                                           {'REST': 'tcp dpt:8443 state NEW limit: up to '
                                                    '100/min burst 10'},
                                           {'DESTINATION': '10.83.182.143',
                                            'OPT': '--',
                                            'PROT': 'tcp',
                                            'REST': 'tcp dpt:8443 state NEW',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'DROP'},
                                           {'REST': 'tcp dpt:8443 state NEW'},
                                           {'DESTINATION': '10.83.182.143',
                                            'OPT': '--',
                                            'PROT': 'udp',
                                            'REST': 'udp spt:53 state ESTABLISHED',
                                            'SOURCE': '10.56.126.31',
                                            'TARGET': 'ACCEPT'},
                                           {'REST': 'udp spt:53 state ESTABLISHED'},
                                           {'DESTINATION': '10.83.182.143',
                                            'OPT': '--',
                                            'PROT': 'tcp',
                                            'REST': 'tcp spt:53 state ESTABLISHED',
                                            'SOURCE': '10.56.126.31',
                                            'TARGET': 'ACCEPT'},
                                           {'REST': 'tcp spt:53 state ESTABLISHED'},
                                           {'DESTINATION': '10.83.182.143',
                                            'OPT': '--',
                                            'PROT': 'udp',
                                            'REST': 'udp spt:123 dpt:123',
                                            'SOURCE': '10.83.200.2',
                                            'TARGET': 'ACCEPT'},
                                           {'REST': 'udp spt:123 dpt:123'},
                                           {'DESTINATION': '10.83.182.143',
                                            'OPT': '--',
                                            'PROT': 'udp',
                                            'REST': 'udp spt:123 dpt:123',
                                            'SOURCE': '10.83.200.3',
                                            'TARGET': 'ACCEPT'},
                                           {'REST': 'udp spt:123 dpt:123'},
                                           {'DESTINATION': '10.83.182.143',
                                            'OPT': '--',
                                            'PROT': 'udp',
                                            'REST': 'udp spt:123 dpt:123',
                                            'SOURCE': '10.83.200.4',
                                            'TARGET': 'ACCEPT'},
                                           {'REST': 'udp spt:123 dpt:123'},
                                           {'DESTINATION': '0.0.0.0/0',
                                            'OPT': '--',
                                            'PROT': 'udp',
                                            'REST': 'udp dpts:33434:33933 limit: avg '
                                                    '25/sec burst 10',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'ACCEPT'},
                                           {'REST': 'udp dpts:33434:33933 limit: avg '
                                                    '25/sec burst 10'},
                                           {'DESTINATION': '0.0.0.0/0',
                                            'OPT': '--',
                                            'PROT': 'udp',
                                            'REST': 'udp dpts:33434:33933',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'DROP'},
                                           {'REST': 'udp dpts:33434:33933'},
                                           {'DESTINATION': '0.0.0.0/0',
                                            'OPT': '--',
                                            'PROT': 'icmp',
                                            'REST': 'icmptype 8 limit: avg 25/sec burst '
                                                    '8',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'ACCEPT'},
                                           {'REST': 'icmptype 8 limit: avg 25/sec burst 8'},
                                           {'DESTINATION': '0.0.0.0/0',
                                            'OPT': '--',
                                            'PROT': 'icmp',
                                            'REST': 'icmptype 8',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'DROP'},
                                           {'REST': 'icmptype 8'},
                                           {'DESTINATION': '0.0.0.0/0',
                                            'OPT': '--',
                                            'PROT': 'icmp',
                                            'REST': 'icmptype 0 limit: avg 25/sec burst '
                                                    '8',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'ACCEPT'},
                                           {'REST': 'icmptype 0 limit: avg 25/sec burst 8'},
                                           {'DESTINATION': '0.0.0.0/0',
                                            'OPT': '--',
                                            'PROT': 'icmp',
                                            'REST': 'icmptype 0',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'DROP'},
                                           {'REST': 'icmptype 0'},
                                           {'DESTINATION': '0.0.0.0/0',
                                            'OPT': '--',
                                            'PROT': 'icmp',
                                            'REST': 'icmptype 3 limit: avg 25/sec burst '
                                                    '8',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'ACCEPT'},
                                           {'REST': 'icmptype 3 limit: avg 25/sec burst 8'},
                                           {'DESTINATION': '0.0.0.0/0',
                                            'OPT': '--',
                                            'PROT': 'icmp',
                                            'REST': 'icmptype 3',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'DROP'},
                                           {'REST': 'icmptype 3'},
                                           {'DESTINATION': '0.0.0.0/0',
                                            'OPT': '--',
                                            'PROT': 'icmp',
                                            'REST': 'icmptype 11 limit: avg 25/sec burst '
                                                    '8',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'ACCEPT'},
                                           {'REST': 'icmptype 11 limit: avg 25/sec burst 8'},
                                           {'DESTINATION': '0.0.0.0/0',
                                            'OPT': '--',
                                            'PROT': 'icmp',
                                            'REST': 'icmptype 11',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'DROP'},
                                           {'REST': 'icmptype 11'},
                                           {'DESTINATION': '10.83.182.143',
                                            'OPT': '--',
                                            'PROT': 'tcp',
                                            'REST': 'tcp dpt:22 state NEW limit: up to '
                                                    '5/sec burst 10 mode srcip '
                                                    'htable-expire 60000',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'ACCEPT'},
                                           {'REST': 'tcp dpt:22 state NEW limit: up to '
                                                    '5/sec burst 10 mode srcip '
                                                    'htable-expire 60000'},
                                           {'DESTINATION': '10.83.182.143',
                                            'OPT': '--',
                                            'PROT': 'tcp',
                                            'REST': 'tcp dpt:22 state NEW',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'DROP'},
                                           {'REST': 'tcp dpt:22 state NEW'},
                                           {'DESTINATION': '10.83.182.143',
                                            'OPT': '--',
                                            'PROT': 'tcp',
                                            'REST': 'tcp dpt:443 state NEW limit: up to '
                                                    '5/sec burst 10 mode srcip '
                                                    'htable-expire 60000',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'ACCEPT'},
                                           {'REST': 'tcp dpt:443 state NEW limit: up to '
                                                    '5/sec burst 10 mode srcip '
                                                    'htable-expire 60000'},
                                           {'DESTINATION': '10.83.182.143',
                                            'OPT': '--',
                                            'PROT': 'tcp',
                                            'REST': 'tcp dpt:443 state NEW',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'DROP'},
                                           {'REST': 'tcp dpt:443 state NEW'},
                                           {'DESTINATION': '0.0.0.0/0',
                                            'OPT': '--',
                                            'PROT': 'tcp',
                                            'REST': 'state RELATED,ESTABLISHED',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'ACCEPT'},
                                           {'REST': 'state RELATED,ESTABLISHED'},
                                           {'DESTINATION': '0.0.0.0/0',
                                            'OPT': '--',
                                            'PROT': 'all',
                                            'SOURCE': '0.0.0.0/0',
                                            'TARGET': 'DROP'}],
                                 'POLICY': 'ACCEPT'}}
