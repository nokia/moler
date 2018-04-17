# -*- coding: utf-8 -*-
"""
Ip_route command module.
"""
import re

from moler.cmd.unix.genericunix import GenericUnix
from moler.cmd.converterhelper import ConverterHelper


__author__ = 'Yang Snackwell'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'snackwell.yang@nokia-sbell.com'


class Ip_route(GenericUnix):

    def __init__(self, connection, prompt=None, new_line_chars=None, is_ipv6=False, addr_get=None, addr_from=None):
        super(Ip_route, self).__init__(connection, prompt, new_line_chars)
        self._converter_helper = ConverterHelper()
        # Parameters defined by calling the command
        self.is_ipv6 = is_ipv6
        self.addr_get = addr_get
        self.addr_from = addr_from
        self.current_ret["VIA"] = dict()
        self.current_ret["ALL"] = []
        self.current_ret["ADDRESS"] = dict()

    def build_command_string(self):
        cmd = "ip route"
        if self.is_ipv6:
            cmd = "ip -6 route"
        if self.addr_get:
            cmd = cmd + " get ".self.addr_get
            if self.addr_from:
                cmd = cmd + " from ".addr_from
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            parsed = False
            parsed = self._parse_via_dev_proto_metric(line, parsed)
            parsed = self._parse_via_dev_proto_expires_mtu_hoplimit(line, parsed)
            parsed = self._parse_via_dev_metric_mtu(line, parsed)
            parsed = self._parse_via_dev_metric(line, parsed)
            parsed = self._parse_via_dev(line, parsed)
            parsed = self._parse_dev_proto_scope_src(line, parsed)
            parsed = self._parse_dev_proto_metric_mtu(line, parsed)
            parsed = self._parse_dev_proto_metric(line, parsed)
            parsed = self._parse_from_src_metric(line, parsed)
            parsed = self._parse_dev_src(line, parsed)
            self._parse_from_via_dev(line, parsed)
        return super(Ip_route, self).on_new_line(line, is_full_line)

    def get_default_route(self):
        def_route = None
        if "VIA" in self.current_ret:
            if "default" in self.current_ret["VIA"]:
                def_route = self.current_ret["VIA"]["default"]["VIA"]
                if "METRIC" in self.current_ret["VIA"]["default"]:
                    metric = self.current_ret["VIA"]["default"]["METRIC"]

                for item in self.current_ret["ALL"]:
                    if "default" == item["ADDRESS"]:
                        if "METRIC" in item:
                            if metric:
                                if item["METRIC"] > metric:
                                    pass
                            def_route = item["VIA"]
                            metric = item["METRIC"]

        return def_route

    def _process_line_address_all(self, line, parsed, regexp):
        if not parsed and self._regex_helper.search_compiled(regexp, line):
            _ret = dict()
            _key_addr = self._regex_helper.group("ADDRESS")
            _ret[_key_addr] = self._regex_helper.groupdict()
            self.current_ret["ADDRESS"][_key_addr] = _ret[_key_addr]
            self.current_ret["ALL"].append(_ret[_key_addr])
            parsed = True
        return parsed

    def _process_line_via_all(self, line, parsed, regexp):
        if not parsed and self._regex_helper.search_compiled(regexp, line):
            _ret = dict()
            _key_addr = self._regex_helper.group("ADDRESS")
            _ret[_key_addr] = self._regex_helper.groupdict()
            self.current_ret["VIA"][_key_addr] = _ret[_key_addr]
            self.current_ret["ALL"].append(_ret[_key_addr])
            parsed = True
        return parsed

    # default via fe80::a00:27ff:fe91:697c dev br0  proto ra  metric 1024  expires 1079sec mtu 1340 hoplimit 64
    _re_via_dev_proto_expires_mtu_hoplimit = re.compile(r"^\s*(?P<ADDRESS>\S+)\s+via\s+(?P<VIA>\S+)\s+"
                                                        r"dev\s+(?P<DEV>\S+)\s+proto\s+(?P<PROTO>\S+)\s+"
                                                        r"metric\s+(?P<EXPIRES>\S+)\s+expires\s+(?P<MTU>\S+)\s+"
                                                        r"mtu\s+(?P<HOPLIMIT>\S+)\s+hoplimit\s+(\S+)$")

    def _parse_via_dev_proto_expires_mtu_hoplimit(self, line, parsed):
        return self._process_line_via_all(line, parsed, Ip_route._re_via_dev_proto_expires_mtu_hoplimit)

    # default via 10.83.225.254 dev eth0  proto none  metric 1
    _re_via_dev_proto_metric = re.compile(r"^\s*(?P<ADDRESS>\S+)\s+via\s+(?P<VIA>\S+)\s+dev\s+(?P<DEV>\S+)\s+"
                                          r"proto\s+(?P<PROTO>\S+)\s+metric\s+(?P<METRIC>\S+)\s*$")

    def _parse_via_dev_proto_metric(self, line, parsed):
        return self._process_line_via_all(line, parsed, Ip_route._re_via_dev_proto_metric)

    # default via 2a00:8a00:6000:7000:1000:4100:151:2 dev br0  metric 1  mtu 1500
    _re_via_dev_metric_mtu = re.compile(r"^\s*(?P<ADDRESS>\S+)\s+via\s+(?P<VIA>\S+)\s+dev\s+(?P<DEV>\S+)\s+"
                                        r"metric\s+(?P<METRIC>\S+)\s+mtu\s+(?P<MTU>\S+)\s*$")

    def _parse_via_dev_metric_mtu(self, line, parsed):
        return self._process_line_via_all(line, parsed, Ip_route._re_via_dev_metric_mtu)

    # default via 2a00:8a00:6000:7000:a00:7900:3:0 dev br0.2605  metric 1
    _re_via_dev_metric = re.compile(r"^\s*(?P<ADDRESS>\S+)\s+via\s+(?P<VIA>\S+)\s+dev\s+(?P<DEV>\S+)\s+"
                                    r"metric\s+(?P<METRIC>\S+)\s*$")

    def _parse_via_dev_metric(self, line, parsed):
        return self._process_line_via_all(line, parsed, Ip_route._re_via_dev_metric)

    # default via 2a00:8a00:6000:7000:1000:4100:151:2 dev br0
    _re_via_dev = re.compile(r"^\s*(?P<ADDRESS>\S+)\s+via\s+(?P<VIA>\S+)\s+dev\s+(?P<DEV>\S+).*$")

    def _parse_via_dev(self, line, parsed):
        return self._process_line_via_all(line, parsed, Ip_route._re_via_dev)

    # 10.83.224.0/23 dev eth0  proto kernel  scope link  src 10.83.225.103
    _re_dev_proto_scope_src = re.compile(r"^\s*(?P<ADDRESS>\S+)\s+dev\s+(?P<DEV>\S+)\s+"
                                         r"proto\s+(?P<PROTO>\S+)\s+scope\s+(?P<SCOPE>\S+)\s+src\s+(?P<SRC>\S+)\s*$")

    def _parse_dev_proto_scope_src(self, line, parsed):
        return self._process_line_address_all(line, parsed, Ip_route._re_dev_proto_scope_src)

    # fe80::/64 dev br0  proto kernel  metric 256  mtu 1632
    _re_dev_proto_metric_mtu = re.compile(r"(?P<ADDRESS>\S+)\s+dev\s+(?P<DEV>\S+)\s+proto\s+(?P<PROTO>\S+)\s+"
                                          r"metric\s+(?P<METRIC>\S+)\s+mtu\s+(?P<MTU>\S+)")

    def _parse_dev_proto_metric_mtu(self, line, parsed):
        return self._process_line_address_all(line, parsed, Ip_route._re_dev_proto_metric_mtu)

    # 2a00:8a00:6000:7000:a00:3900::/96 dev br0.2607  proto kernel  metric 256
    _re_dev_proto_metric = re.compile(r"(?P<ADDRESS>\S+)\s+dev\s+(?P<DEV>\S+)\s+proto\s+(?P<PROTO>\S+)\s+"
                                      r"metric\s+(?P<METRIC>\S+)")

    def _parse_dev_proto_metric(self, line, parsed):
        return self._process_line_address_all(line, parsed, Ip_route._re_dev_proto_metric)

    # 2000::2011 from :: dev eth3  src 2000::2012  metric 0
    _re_from_src_metric = re.compile(r"(?P<ADDRESS>\S+)\s+from\s+(?P<FROM>\S+)\s+dev\s+(?P<DEV>\S+)\s+"
                                     r"src\s+(?P<SRC>\S+)\s+metric\s+(?P<METRIC>\d+)")

    def _parse_from_src_metric(self, line, parsed):
        return self._process_line_address_all(line, parsed, Ip_route._re_from_src_metric)

    # 10.0.0.249 dev eth3  src 10.0.0.2
    _re_dev_src = re.compile(r"(?P<ADDRESS>\S+)\s+dev\s+(?P<DEV>\S+)\s+src\s+(?P<SRC>\S+)")

    def _parse_dev_src(self, line, parsed):
        return self._process_line_address_all(line, parsed, Ip_route._re_dev_src)

    # ip route get 99.99.99.99 from 10.0.0.249
    # 99.99.99.99 from 10.0.0.249 via 10.0.0.2 dev br0
    _re_from_via_dev = re.compile(r"(?P<ADDRESS>\S+)\s+from\s+(?P<FROM>\S+)\s+via\s+(?P<VIA>\S+)\s+dev\s+(?P<DEV>\S+)")

    def _parse_from_via_dev(self, line, parsed):
        return self._process_line_address_all(line, parsed, Ip_route._re_from_via_dev)


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
 host:~ # """

COMMAND_KWARGS_ver_human = {}

COMMAND_RESULT_ver_human = {
    'ADDRESS': {'10.0.0.0/24': {'ADDRESS': '10.0.0.0/24',
                                'DEV': 'eth3',
                                'PROTO': 'kernel',
                                'SCOPE': 'link',
                                'SRC': '10.0.0.2'},
                '10.83.200.0/21': {'ADDRESS': '10.83.200.0/21',
                                   'DEV': 'eth0',
                                   'PROTO': 'kernel',
                                   'SCOPE': 'link',
                                   'SRC': '10.83.204.18'},
                '10.89.5.0/25': {'ADDRESS': '10.89.5.0/25',
                                 'DEV': 'eth2',
                                 'PROTO': 'kernel',
                                 'SCOPE': 'link',
                                 'SRC': '10.89.5.52'},
                '192.168.255.0/24': {'ADDRESS': '192.168.255.0/24',
                                     'DEV': 'eth1',
                                     'PROTO': 'kernel',
                                     'SCOPE': 'link',
                                     'SRC': '192.168.255.126'},
                '41.1.0.0/20': {'ADDRESS': '41.1.0.0/20',
                                'DEV': 'tunPGW',
                                'PROTO': 'kernel',
                                'SCOPE': 'link',
                                'SRC': '41.1.1.254'}},
    'ALL': [{'ADDRESS': 'default', 'DEV': 'eth0', 'VIA': '10.83.207.254'},
            {'ADDRESS': '10.0.0.0/24',
             'DEV': 'eth3',
             'PROTO': 'kernel',
             'SCOPE': 'link',
             'SRC': '10.0.0.2'},
            {'ADDRESS': '10.1.52.248', 'DEV': 'eth3', 'VIA': '10.0.0.248'},
            {'ADDRESS': '10.83.200.0/21',
             'DEV': 'eth0',
             'PROTO': 'kernel',
             'SCOPE': 'link',
             'SRC': '10.83.204.18'},
            {'ADDRESS': '10.83.224.0/23', 'DEV': 'eth2', 'VIA': '10.89.5.126'},
            {'ADDRESS': '10.89.5.0/25',
             'DEV': 'eth2',
             'PROTO': 'kernel',
             'SCOPE': 'link',
             'SRC': '10.89.5.52'},
            {'ADDRESS': '10.254.0.0/16', 'DEV': 'eth2', 'VIA': '10.89.5.126'},
            {'ADDRESS': '41.1.0.0/20',
             'DEV': 'tunPGW',
             'PROTO': 'kernel',
             'SCOPE': 'link',
             'SRC': '41.1.1.254'},
            {'ADDRESS': '192.168.255.0/24',
             'DEV': 'eth1',
             'PROTO': 'kernel',
             'SCOPE': 'link',
             'SRC': '192.168.255.126'}],
    'VIA': {'10.1.52.248': {'ADDRESS': '10.1.52.248',
                            'DEV': 'eth3',
                            'VIA': '10.0.0.248'},
            '10.254.0.0/16': {'ADDRESS': '10.254.0.0/16',
                              'DEV': 'eth2',
                              'VIA': '10.89.5.126'},
            '10.83.224.0/23': {'ADDRESS': '10.83.224.0/23',
                               'DEV': 'eth2',
                               'VIA': '10.89.5.126'},
            'default': {'ADDRESS': 'default',
                        'DEV': 'eth0',
                        'VIA': '10.83.207.254'}}
}
