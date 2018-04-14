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

    # ====== Group for ^ xxx via * $======
    _re_via_pattern_group = re.compile(r"^\s*\S+\s+via\s+")

    # default via 10.83.225.254 dev eth0  proto none  metric 1
    _re_via_dev_proto_metric = re.compile(r"^\s*(\S+)\s+via\s+(\S+)\s+dev\s+(\S+)\s+proto\s+(\S+)\s+metric\s+(\S+)\s*$")

    # default via fe80::a00:27ff:fe91:697c dev br0  proto ra  metric 1024  expires 1079sec mtu 1340 hoplimit 64
    _re_via_dev_proto_expires_mtu_hoplimit = re.compile(
        r"^\s*(\S+)\s+via\s+(\S+)\s+dev\s+(\S+)\s+proto\s+(\S+)\s+metric\s+(\S+)\s+expires\s+(\S+)\s+mtu\s+(\S+)\s+hoplimit\s+(\S+)$")

    # default via 2a00:8a00:6000:7000:a00:7900:3:0 dev br0.2605  metric 1
    _re_via_dev_metric = re.compile(r"^\s*(\S+)\s+via\s+(\S+)\s+dev\s+(\S+)\s+metric\s+(\S+)\s*$")

    # default via 2a00:8a00:6000:7000:1000:4100:151:2 dev br0  metric 1  mtu 1500
    _re_via_dev_metric_mtu = re.compile(r"^\s*(\S+)\s+via\s+(\S+)\s+dev\s+(\S+)\s+metric\s+(\S+)\s+mtu\s+(\S+)\s*$")

    # default via 2a00:8a00:6000:7000:1000:4100:151:2 dev br0
    _re_via_dev = re.compile(r"^\s*(\S+)\s+via\s+(\S+)\s+dev\s+(\S+).*$")

    # ======= Group for ^ xxx dev * $ =======
    _re_dev_pattern_group = re.compile(r"^\s*(\S+)\s+dev\s+")

    # 10.83.224.0/23 dev eth0  proto kernel  scope link  src 10.83.225.103
    _re_dev_proto_scope_src = re.compile(r"^\s*(\S+)\s+dev\s+(\S+)\s+proto\s+(\S+)\s+scope\s+(\S+)\s+src\s+(\S+)\s*$")

    # fe80::/64 dev br0  proto kernel  metric 256  mtu 1632
    _re_dev_proto_metric_mtu = re.compile(r"(\S+)\s+dev\s+(\S+)\s+proto\s+(\S+)\s+metric\s+(\S+)\s+mtu\s+(\S+)")

    # 2a00:8a00:6000:7000:a00:3900::/96 dev br0.2607  proto kernel  metric 256
    _re_dev_proto_metric = re.compile(r"(\S+)\s+dev\s+(\S+)\s+proto\s+(\S+)\s+metric\s+(\S+)")

    # 10.0.0.249 dev eth3  src 10.0.0.2
    _re_dev_src = re.compile(r"(\S+)\s+dev\s+(\S+)\s+src\s+(\S+)")

    # ======= Group for ^ xxx from * $ =======
    _re_from_pattern_group = re.compile(r"(\S+)\s+from\s+")

    # 2000::2011 from :: dev eth3  src 2000::2012  metric 0
    _re_from_src_metric = re.compile(r"(\S+)\s+from\s+(\S+)\s+dev\s+(\S+)\s+src\s+(\S+)\s+metric\s+(\d+)")

    # ip route get 99.99.99.99 from 10.0.0.249
    # 99.99.99.99 from 10.0.0.249 via 10.0.0.2 dev br0
    _re_from_via_dev = re.compile(r"(\S+)\s+from\s+(\S+)\s+via\s+(\S+)\s+dev\s+(\S+)")

    def __init__(self, connection, prompt=None, new_line_chars=None, is_ipv6=False, addr_get=None, addr_from=None):
        super(Ip_route, self).__init__(connection, prompt, new_line_chars)
        self._converter_helper = ConverterHelper()
        # Parameters defined by calling the command
        self.is_ipv6 = is_ipv6
        self.addr_get = addr_get
        self.addr_from = addr_from
        self.matched = 0
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

    def _parse_re_via_dev_proto_metric(self):
        _ret = dict()
        _key_addr = self._regex_helper.group(1)
        _ret[_key_addr] = dict()
        _ret[_key_addr]["ADDRESS"] = self._regex_helper.group(1)
        _ret[_key_addr]["VIA"] = self._regex_helper.group(2)
        _ret[_key_addr]["DEV"] = self._regex_helper.group(3)
        _ret[_key_addr]["PROTO"] = self._regex_helper.group(4)
        _ret[_key_addr]["METRIC"] = self._regex_helper.group(5)
        self.current_ret["VIA"][_key_addr] = _ret[_key_addr]
        self.current_ret["ALL"].append(_ret[_key_addr])

    def _parse_re_via_dev_proto_expires_mtu_hoplimit(self):
        _ret = dict()
        _key_addr = self._regex_helper.group(1)
        _ret[_key_addr] = dict()
        _ret[_key_addr]["ADDRESS"] = self._regex_helper.group(1)
        _ret[_key_addr]["VIA"] = self._regex_helper.group(2)
        _ret[_key_addr]["DEV"] = self._regex_helper.group(3)
        _ret[_key_addr]["PROTO"] = self._regex_helper.group(4)
        _ret[_key_addr]["EXPIRES"] = self._regex_helper.group(5)
        _ret[_key_addr]["MTU"] = self._regex_helper.group(6)
        _ret[_key_addr]["HOPLIMIT"] = self._regex_helper.group(7)
        self.current_ret["VIA"][_key_addr] = _ret[_key_addr]
        self.current_ret["ALL"].append(_ret[_key_addr])

    def _parse_re_via_dev_metric_mtu(self):
        _ret = dict()
        _key_addr = self._regex_helper.group(1)
        _ret[_key_addr] = dict()
        _ret[_key_addr]["ADDRESS"] = self._regex_helper.group(1)
        _ret[_key_addr]["VIA"] = self._regex_helper.group(2)
        _ret[_key_addr]["DEV"] = self._regex_helper.group(3)
        _ret[_key_addr]["METRIC"] = self._regex_helper.group(4)
        _ret[_key_addr]["MTU"] = self._regex_helper.group(5)
        self.current_ret["VIA"][_key_addr] = _ret[_key_addr]
        self.current_ret["ALL"].append(_ret[_key_addr])

    def _parse_re_via_dev_metric(self):
        _ret = dict()
        _key_addr = self._regex_helper.group(1)
        _ret[_key_addr] = dict()
        _ret[_key_addr]["ADDRESS"] = self._regex_helper.group(1)
        _ret[_key_addr]["VIA"] = self._regex_helper.group(2)
        _ret[_key_addr]["DEV"] = self._regex_helper.group(3)
        _ret[_key_addr]["METRIC"] = self._regex_helper.group(4)
        self.current_ret["VIA"][_key_addr] = _ret[_key_addr]
        self.current_ret["ALL"].append(_ret[_key_addr])

    def _parse_re_via_dev(self):
        _ret = dict()
        _key_addr = self._regex_helper.group(1)
        _ret[_key_addr] = dict()
        _ret[_key_addr]["ADDRESS"] = self._regex_helper.group(1)
        _ret[_key_addr]["VIA"] = self._regex_helper.group(2)
        _ret[_key_addr]["DEV"] = self._regex_helper.group(3)
        self.current_ret["VIA"][_key_addr] = _ret[_key_addr]
        self.current_ret["ALL"].append(_ret[_key_addr])

    def _parse_re_dev_proto_scope_src(self):
        _ret = dict()
        _key_addr = self._regex_helper.group(1)
        _ret[_key_addr] = dict()
        _ret[_key_addr]["ADDRESS"] = self._regex_helper.group(1)
        _ret[_key_addr]["DEV"] = self._regex_helper.group(2)
        _ret[_key_addr]["PROTO"] = self._regex_helper.group(3)
        _ret[_key_addr]["SCOPE"] = self._regex_helper.group(4)
        _ret[_key_addr]["SRC"] = self._regex_helper.group(5)
        self.current_ret["ADDRESS"][_key_addr] = _ret[_key_addr]
        self.current_ret["ALL"].append(_ret[_key_addr])

    def _parse_re_dev_proto_metric_mtu(self):
        _ret = dict()
        _key_addr = self._regex_helper.group(1)
        _ret[_key_addr] = dict()
        _ret[_key_addr]["ADDRESS"] = self._regex_helper.group(1)
        _ret[_key_addr]["DEV"] = self._regex_helper.group(2)
        _ret[_key_addr]["PROTO"] = self._regex_helper.group(3)
        _ret[_key_addr]["METRIC"] = self._regex_helper.group(4)
        _ret[_key_addr]["MTU"] = self._regex_helper.group(5)
        self.current_ret["ADDRESS"][_key_addr] = _ret[_key_addr]
        self.current_ret["ALL"].append(_ret[_key_addr])

    def _parse_re_dev_proto_metric(self):
        _ret = dict()
        _key_addr = self._regex_helper.group(1)
        _ret[_key_addr] = dict()
        _ret[_key_addr]["ADDRESS"] = self._regex_helper.group(1)
        _ret[_key_addr]["DEV"] = self._regex_helper.group(2)
        _ret[_key_addr]["PROTO"] = self._regex_helper.group(3)
        _ret[_key_addr]["METRIC"] = self._regex_helper.group(4)
        self.current_ret["ADDRESS"][_key_addr] = _ret[_key_addr]
        self.current_ret["ALL"].append(_ret[_key_addr])

    def _parse_re_from_src_metric(self):
        _ret = dict()
        _key_addr = self._regex_helper.group(1)
        _ret[_key_addr] = dict()
        _ret[_key_addr]["ADDRESS"] = self._regex_helper.group(1)
        _ret[_key_addr]["FROM"] = self._regex_helper.group(2)
        _ret[_key_addr]["SRC"] = self._regex_helper.group(3)
        _ret[_key_addr]["METRIC"] = self._regex_helper.group(4)
        self.current_ret["ADDRESS"][_key_addr] = _ret[_key_addr]
        self.current_ret["ALL"].append(_ret[_key_addr])

    def _parse_re_dev_src(self):
        _ret = dict()
        _key_addr = self._regex_helper.group(1)
        _ret[_key_addr] = dict()
        _ret[_key_addr]["ADDRESS"] = self._regex_helper.group(1)
        _ret[_key_addr]["DEV"] = self._regex_helper.group(2)
        _ret[_key_addr]["SRC"] = self._regex_helper.group(3)
        self.current_ret["ADDRESS"][_key_addr] = _ret[_key_addr]
        self.current_ret["ALL"].append(_ret[_key_addr])

    def _parse_re_from_via_dev(self):
        _ret = dict()
        _key_addr = self._regex_helper.group(1)
        _ret[_key_addr] = dict()
        _ret[_key_addr]["ADDRESS"] = self._regex_helper.group(1)
        _ret[_key_addr]["FROM"] = self._regex_helper.group(2)
        _ret[_key_addr]["VIA"] = self._regex_helper.group(3)
        _ret[_key_addr]["DEV"] = self._regex_helper.group(4)
        self.current_ret["ADDRESS"][_key_addr] = _ret[_key_addr]
        self.current_ret["ALL"].append(_ret[_key_addr])

    def _process_re_via_pattern_group(self, line):
        # _re_via_dev_proto_metric
        if self._regex_helper.search_compiled(Ip_route._re_via_dev_proto_metric, line):
            self._parse_re_via_dev_proto_metric()
        # _re_via_dev_proto_expires_mtu_hoplimit
        elif self._regex_helper.search_compiled(Ip_route._re_via_dev_proto_expires_mtu_hoplimit, line):
            self._parse_re_via_dev_proto_expires_mtu_hoplimit()
        # _re_via_dev_metric_mtu
        elif self._regex_helper.search_compiled(Ip_route._re_via_dev_metric_mtu, line):
            self._parse_re_via_dev_metric_mtu()
        # _re_via_dev_metric
        elif self._regex_helper.search_compiled(Ip_route._re_via_dev_metric, line):
            self._parse_re_via_dev_metric()
        # _re_via_dev
        elif self._regex_helper.search_compiled(Ip_route._re_via_dev, line):
            self._parse_re_via_dev()

    def _process_re_dev_pattern_group(self,line):
        # _re_dev_proto_scope_src
        if self._regex_helper.search_compiled(Ip_route._re_dev_proto_scope_src, line):
            self._parse_re_dev_proto_scope_src()
        # _re_dev_proto_metric_mtu
        elif self._regex_helper.search_compiled(Ip_route._re_dev_proto_metric_mtu, line):
            self._parse_re_dev_proto_metric_mtu()
        # _re_dev_proto_metric
        elif self._regex_helper.search_compiled(Ip_route._re_dev_proto_metric, line):
            self._parse_re_dev_proto_metric()
        # _re_dev_src
        elif self._regex_helper.search_compiled(Ip_route._re_dev_src, line):
            self._parse_re_dev_src()

    def _process_re_from_pattern_group(self,line):
        # _re_from_src_metric
        if self._regex_helper.search_compiled(Ip_route._re_from_src_metric, line):
            self._parse_re_from_src_metric()
        # _re_from_via_dev
        elif self._regex_helper.search_compiled(Ip_route._re_from_via_dev, line):
            self._parse_re_from_via_dev()

    def on_new_line(self, line, is_full_line):
        if not is_full_line:
            return super(Ip_route, self).on_new_line(line, is_full_line)

        # _re_via_pattern_group
        if self._regex_helper.search_compiled(Ip_route._re_via_pattern_group, line):
            self._process_re_via_pattern_group(line)
        elif self._regex_helper.search_compiled(Ip_route._re_dev_pattern_group, line):
            self._process_re_dev_pattern_group(line)
        elif self._regex_helper.search_compiled(Ip_route._re_from_pattern_group, line):
            self._process_re_from_pattern_group(line)

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
