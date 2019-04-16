# -*- coding: utf-8 -*-
"""
ifconfig command module.
"""

__author__ = 'Sylwester Golonka, Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'sylwester.golonka@nokia.com, michal.ernst@nokia.com'

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone


class Ifconfig(GenericUnixCommand):
    def __init__(self, connection, options=None, prompt=None, newline_chars=None, runner=None):
        super(Ifconfig, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                       runner=runner)
        # Parameters defined by calling the command
        self.ret_required = False
        self.if_name = None
        self.options = options

    def build_command_string(self):
        cmd = "ifconfig"
        if self.options:
            cmd = cmd + " " + self.options
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_interface(line)
                self._parse_rx_packets(line)
                self._parse_tx_packets(line)
                self._parse_rx_tx_bytes(line)
                self._parse_content(line)
                self._parse_link(line)
                self._parse_v4_brd(line)
                self._parse_v4(line)
                self._parse_v6(line)
            except ParsingDone:
                pass
        return super(Ifconfig, self).on_new_line(line, is_full_line)

    def _process_line(self, line, regexp, key_list, dict_type):
        if self._regex_helper.search_compiled(regexp, line):
            _ret = dict()
            for key in key_list:
                _ret[key] = self._regex_helper.group(key)

            if not self.current_ret[self.if_name][dict_type][0]:
                self.current_ret[self.if_name][dict_type][0] = _ret
            else:
                self.current_ret[self.if_name][dict_type].append(_ret)
            raise ParsingDone

    _re_ip_v4_brd = re.compile(
        r"inet addr:(?P<IP>\d+\.\d+\.\d+\.\d+)\s\sBcast:(?P<BRD>\d+\.\d+\.\d+\.\d+)\s\sMask:(?P<MASK>\d+\.\d+\.\d+\.\d+)")
    _key_ip_v4_brd = ["IP", "BRD", "MASK"]

    def _parse_v4_brd(self, line):
        return self._process_line(line, Ifconfig._re_ip_v4_brd, Ifconfig._key_ip_v4_brd, "IPV4")

    _re_ip_v4 = re.compile(r"inet addr:(?P<IP>\d+\.\d+\.\d+\.\d+)\s\sMask:(?P<MASK>\d+\.\d+\.\d+\.\d+)")
    _key_ip_v4 = ["IP", "MASK"]

    def _parse_v4(self, line):
        return self._process_line(line, Ifconfig._re_ip_v4, Ifconfig._key_ip_v4, "IPV4")

    _re_ip_v6 = re.compile(r"inet6\saddr:\s(?P<IP>.*)\/(?P<MASK>\d+)\sScope:(?P<SCOPE>\S*)")
    _key_ip_v6 = ["IP", "MASK", "SCOPE"]

    def _parse_v6(self, line):
        return self._process_line(line, Ifconfig._re_ip_v6, Ifconfig._key_ip_v6, "IPV6")

    _re_link = re.compile(r"Link\sencap:(?P<ENCAP>\S*)\s\sHWaddr\s(?P<MAC>\S*)")
    _key_link = ["ENCAP", "MAC"]

    def _parse_link(self, line):
        return self._process_line(line, Ifconfig._re_link, Ifconfig._key_link, "LINK")

    _re_interface = re.compile(r"^(?P<INTERFACE>\S+)\s+(.+)$")

    def _parse_interface(self, line):
        if self._regex_helper.search_compiled(Ifconfig._re_interface, line):
            self.current_ret[self._regex_helper.group("INTERFACE")] = {"IPV4": [{}], "IPV6": [{}], "LINK": [{}],
                                                                       "CONTENT": []}
            self.if_name = self._regex_helper.group("INTERFACE")

    _re_content = re.compile(r"^\s+(?P<CONTENT>\w+.*)")

    def _parse_content(self, line):
        if self._regex_helper.search_compiled(Ifconfig._re_content, line):
            self.current_ret[self.if_name]["CONTENT"].append(self._regex_helper.group("CONTENT"))

    def _prepare_rx_tx_result_keys(self):
        if "RX" not in self.current_ret[self.if_name]:
            self.current_ret[self.if_name]["RX"] = dict()
            self.current_ret[self.if_name]["RX"]["packets"] = dict()
            self.current_ret[self.if_name]["RX"]["bytes"] = dict()
        if "TX" not in self.current_ret[self.if_name]:
            self.current_ret[self.if_name]["TX"] = dict()
            self.current_ret[self.if_name]["TX"]["packets"] = dict()
            self.current_ret[self.if_name]["TX"]["bytes"] = dict()

    # RX packets:3625 errors:0 dropped:0 overruns:0 frame:0
    _re_rx_packets = re.compile(
        r"RX packets:(?P<PACKETS>\d+)\s+errors:(?P<ERRORS>\d+)\s+dropped:(?P<DROPPED>\d+)\s+overruns:(?P<OVERRUNS>\d+)\s+frame:(?P<FRAME>\d+)")

    def _parse_rx_packets(self, line):
        if self._regex_helper.search_compiled(Ifconfig._re_rx_packets, line):
            self._prepare_rx_tx_result_keys()
            self.current_ret[self.if_name]["RX"]["packets"] = {
                "packets": self._regex_helper.group("PACKETS"),
                "errors": self._regex_helper.group("ERRORS"),
                "dropped": self._regex_helper.group("DROPPED"),
                "overruns": self._regex_helper.group("OVERRUNS"),
                "frame": self._regex_helper.group("FRAME"),
            }

            raise ParsingDone

    # TX packets:18083 errors:0 dropped:0 overruns:0 carrier:0
    _re_tx_packets = re.compile(
        r"TX packets:(?P<PACKETS>\d+)\s+errors:(?P<ERRORS>\d+)\s+dropped:(?P<DROPPED>\d+)\s+overruns:(?P<OVERRUNS>\d+)\s+carrier:(?P<CARRIER>\d+)")

    def _parse_tx_packets(self, line):
        if self._regex_helper.search_compiled(Ifconfig._re_tx_packets, line):
            self._prepare_rx_tx_result_keys()
            self.current_ret[self.if_name]["TX"]["packets"] = {
                "packets": self._regex_helper.group("PACKETS"),
                "errors": self._regex_helper.group("ERRORS"),
                "dropped": self._regex_helper.group("DROPPED"),
                "overruns": self._regex_helper.group("OVERRUNS"),
                "carrier": self._regex_helper.group("CARRIER"),
            }

            raise ParsingDone

    # RX bytes:630550 (615.7 KiB)  TX bytes:2560834 (2.4 MiB)
    _re_rx_tx_bytes = re.compile(r"RX bytes:(?P<RX_BYTES>\d+).*TX bytes:(?P<TX_BYTES>\d+)")

    def _parse_rx_tx_bytes(self, line):
        if self._regex_helper.search_compiled(Ifconfig._re_rx_tx_bytes, line):
            self._prepare_rx_tx_result_keys()
            self.current_ret[self.if_name]["RX"]["bytes"] = {
                "bytes_raw": self._regex_helper.group("RX_BYTES"),
            }
            self.current_ret[self.if_name]["TX"]["bytes"] = {
                "bytes_raw": self._regex_helper.group("TX_BYTES"),
            }

            raise ParsingDone


COMMAND_OUTPUT = """
root@fzm-lsp-k2:~# ifconfig
br0       Link encap:Ethernet  HWaddr 60:a8:fe:74:f8:ab
          inet addr:10.0.0.64  Bcast:10.0.0.255  Mask:255.255.255.0
          inet addr:10.0.0.65  Bcast:10.0.0.255  Mask:255.255.255.0
          inet6 addr: fe80::a00:27ff:fe30:a67e/64 Scope:Link
          UP BROADCAST RUNNING ALLMULTI  MTU:1500  Metric:1
          RX packets:3625 errors:0 dropped:0 overruns:0 frame:0
          TX packets:18083 errors:0 dropped:0 overruns:0 carrier:0
          collisions:0 txqueuelen:0
          RX bytes:630550 (615.7 KiB)  TX bytes:2560834 (2.4 MiB)
container-br0 Link encap:Ethernet  HWaddr fe:4f:f5:ca:67:ec
          inet addr:192.168.255.61  Bcast:192.168.255.63  Mask:255.255.255.252
          UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1
          RX packets:0 errors:0 dropped:0 overruns:0 frame:0
          TX packets:6 errors:0 dropped:0 overruns:0 carrier:0
          collisions:0 txqueuelen:0
          RX bytes:0 (0.0 B)  TX bytes:468 (468.0 B)
eth0      Link encap:Ethernet  HWaddr 60:a8:fe:74:f8:a9
          UP BROADCAST RUNNING ALLMULTI MULTICAST  MTU:1500  Metric:1
          RX packets:3111 errors:0 dropped:0 overruns:0 frame:0
          TX packets:18597 errors:0 dropped:0 overruns:0 carrier:0
          collisions:0 txqueuelen:1000
          RX bytes:378560 (369.6 KiB)  TX bytes:2863574 (2.7 MiB)
eth1      Link encap:Ethernet  HWaddr b4:99:4c:b7:11:ab
          inet addr:192.168.255.129  Bcast:192.168.255.255  Mask:255.255.255.0
          UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1
          RX packets:2447 errors:0 dropped:0 overruns:0 frame:0
          TX packets:47164 errors:0 dropped:0 overruns:0 carrier:0
          collisions:0 txqueuelen:1000
          RX bytes:344845 (336.7 KiB)  TX bytes:44222585 (42.1 MiB)
eth1:2    Link encap:Ethernet  HWaddr b4:99:4c:b7:11:ab
          inet addr:192.168.255.1  Bcast:0.0.0.0  Mask:255.255.254.0
          UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1
eth1:3    Link encap:Ethernet  HWaddr b4:99:4c:b7:11:ab
          inet addr:192.168.255.16  Bcast:192.168.255.19  Mask:255.255.255.252
          UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1
eth3      Link encap:Ethernet  HWaddr 60:a8:fe:74:f8:aa
          UP BROADCAST RUNNING ALLMULTI MULTICAST  MTU:1500  Metric:1
          RX packets:514 errors:0 dropped:0 overruns:0 frame:0
          TX packets:8 errors:0 dropped:0 overruns:0 carrier:0
          collisions:0 txqueuelen:1000
          RX bytes:302740 (295.6 KiB)  TX bytes:1799 (1.7 KiB)
ifb0      Link encap:Ethernet  HWaddr c2:e8:cd:86:73:2b
          UP BROADCAST RUNNING NOARP  MTU:1500  Metric:1
          RX packets:0 errors:0 dropped:0 overruns:0 frame:0
          TX packets:0 errors:0 dropped:0 overruns:0 carrier:0
          collisions:0 txqueuelen:32
          RX bytes:0 (0.0 B)  TX bytes:0 (0.0 B)
lo        Link encap:Local Loopback
          inet addr:127.0.0.1  Mask:255.0.0.0
          inet6 addr: ::1/128 Scope:Host
          UP LOOPBACK RUNNING  MTU:65536  Metric:1
          RX packets:9385 errors:0 dropped:0 overruns:0 frame:0
          TX packets:9385 errors:0 dropped:0 overruns:0 carrier:0
          collisions:0 txqueuelen:0
          RX bytes:10427526 (9.9 MiB)  TX bytes:10427526 (9.9 MiB)
pan0      Link encap:Ethernet  HWaddr 82:1b:5b:02:c9:dc
          inet addr:192.168.255.245  Bcast:192.168.255.247  Mask:255.255.255.248
          UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1
          RX packets:0 errors:0 dropped:0 overruns:0 frame:0
          TX packets:0 errors:0 dropped:0 overruns:0 carrier:0
          collisions:0 txqueuelen:0
          RX bytes:0 (0.0 B)  TX bytes:0 (0.0 B)
pan0:1    Link encap:Ethernet  HWaddr 82:1b:5b:02:c9:dc
          inet addr:192.168.255.241  Bcast:192.168.255.247  Mask:255.255.255.248
          UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1
pan0:2    Link encap:Ethernet  HWaddr 82:1b:5b:02:c9:dc
          inet addr:192.168.255.242  Bcast:192.168.255.247  Mask:255.255.255.248
          UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1

root@fzm-lsp-k2:~#
"""
COMMAND_KWARGS = {}
COMMAND_RESULT = {
    u'br0': {
        'RX': {'bytes': {'bytes_raw': '630550'},
               'packets': {'dropped': '0',
                           'errors': '0',
                           'frame': '0',
                           'overruns': '0',
                           'packets': '3625'}},
        'TX': {'bytes': {'bytes_raw': '2560834'},
               'packets': {'carrier': '0',
                           'dropped': '0',
                           'errors': '0',
                           'overruns': '0',
                           'packets': '18083'}},
        'CONTENT': [u'inet addr:10.0.0.64  Bcast:10.0.0.255  Mask:255.255.255.0',
                    u'inet addr:10.0.0.65  Bcast:10.0.0.255  Mask:255.255.255.0',
                    u'inet6 addr: fe80::a00:27ff:fe30:a67e/64 Scope:Link',
                    u'UP BROADCAST RUNNING ALLMULTI  MTU:1500  Metric:1',
                    u'collisions:0 txqueuelen:0'],
        'IPV4': [{'BRD': u'10.0.0.255',
                  'IP': u'10.0.0.64',
                  'MASK': u'255.255.255.0'},
                 {'BRD': u'10.0.0.255',
                  'IP': u'10.0.0.65',
                  'MASK': u'255.255.255.0'}],
        'IPV6': [{'IP': u'fe80::a00:27ff:fe30:a67e',
                  'MASK': u'64',
                  'SCOPE': u'Link'}],
        'LINK': [{'ENCAP': u'Ethernet',
                  'MAC': u'60:a8:fe:74:f8:ab'}]},
    u'container-br0': {
        'RX': {'bytes': {'bytes_raw': '0'},
               'packets': {'dropped': '0',
                           'errors': '0',
                           'frame': '0',
                           'overruns': '0',
                           'packets': '0'}},
        'TX': {'bytes': {'bytes_raw': '468'},
               'packets': {'carrier': '0',
                           'dropped': '0',
                           'errors': '0',
                           'overruns': '0',
                           'packets': '6'}},
        'CONTENT': [u'inet addr:192.168.255.61  Bcast:192.168.255.63  Mask:255.255.255.252',
                    u'UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1',
                    u'collisions:0 txqueuelen:0'],
        'IPV4': [{'BRD': u'192.168.255.63',
                  'IP': u'192.168.255.61',
                  'MASK': u'255.255.255.252'}],
        'IPV6': [{}],
        'LINK': [{'ENCAP': u'Ethernet',
                  'MAC': u'fe:4f:f5:ca:67:ec'}]},
    u'eth0': {
        'RX': {'bytes': {'bytes_raw': '378560'},
               'packets': {'dropped': '0',
                           'errors': '0',
                           'frame': '0',
                           'overruns': '0',
                           'packets': '3111'}},
        'TX': {'bytes': {'bytes_raw': '2863574'},
               'packets': {'carrier': '0',
                           'dropped': '0',
                           'errors': '0',
                           'overruns': '0',
                           'packets': '18597'}},
        'CONTENT': [u'UP BROADCAST RUNNING ALLMULTI MULTICAST  MTU:1500  Metric:1',
                    u'collisions:0 txqueuelen:1000'],
        'IPV4': [{}],
        'IPV6': [{}],
        'LINK': [{'ENCAP': u'Ethernet',
                  'MAC': u'60:a8:fe:74:f8:a9'}]},
    u'eth1': {
        'RX': {'bytes': {'bytes_raw': '344845'},
               'packets': {'dropped': '0',
                           'errors': '0',
                           'frame': '0',
                           'overruns': '0',
                           'packets': '2447'}},
        'TX': {'bytes': {'bytes_raw': '44222585'},
               'packets': {'carrier': '0',
                           'dropped': '0',
                           'errors': '0',
                           'overruns': '0',
                           'packets': '47164'}},
        'CONTENT': [u'inet addr:192.168.255.129  Bcast:192.168.255.255  Mask:255.255.255.0',
                    u'UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1',
                    u'collisions:0 txqueuelen:1000'],
        'IPV4': [{'BRD': u'192.168.255.255',
                  'IP': u'192.168.255.129',
                  'MASK': u'255.255.255.0'}],
        'IPV6': [{}],
        'LINK': [{'ENCAP': u'Ethernet',
                  'MAC': u'b4:99:4c:b7:11:ab'}]},
    u'eth1:2': {
        'CONTENT': [u'inet addr:192.168.255.1  Bcast:0.0.0.0  Mask:255.255.254.0',
                    u'UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1'],
        'IPV4': [{'BRD': u'0.0.0.0',
                  'IP': u'192.168.255.1',
                  'MASK': u'255.255.254.0'}],
        'IPV6': [{}],
        'LINK': [{'ENCAP': u'Ethernet',
                  'MAC': u'b4:99:4c:b7:11:ab'}]},
    u'eth1:3': {'CONTENT': [u'inet addr:192.168.255.16  Bcast:192.168.255.19  Mask:255.255.255.252',
                            u'UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1'],
                'IPV4': [{'BRD': u'192.168.255.19',
                          'IP': u'192.168.255.16',
                          'MASK': u'255.255.255.252'}],
                'IPV6': [{}],
                'LINK': [{'ENCAP': u'Ethernet',
                          'MAC': u'b4:99:4c:b7:11:ab'}]},
    u'eth3': {
        'RX': {'bytes': {'bytes_raw': '302740'},
               'packets': {'dropped': '0',
                           'errors': '0',
                           'frame': '0',
                           'overruns': '0',
                           'packets': '514'}},
        'TX': {'bytes': {'bytes_raw': '1799'},
               'packets': {'carrier': '0',
                           'dropped': '0',
                           'errors': '0',
                           'overruns': '0',
                           'packets': '8'}},
        'CONTENT': [u'UP BROADCAST RUNNING ALLMULTI MULTICAST  MTU:1500  Metric:1',
                    u'collisions:0 txqueuelen:1000'],
        'IPV4': [{}],
        'IPV6': [{}],
        'LINK': [{'ENCAP': u'Ethernet',
                  'MAC': u'60:a8:fe:74:f8:aa'}]},
    u'ifb0': {
        'RX': {'bytes': {'bytes_raw': '0'},
               'packets': {'dropped': '0',
                           'errors': '0',
                           'frame': '0',
                           'overruns': '0',
                           'packets': '0'}},
        'TX': {'bytes': {'bytes_raw': '0'},
               'packets': {'carrier': '0',
                           'dropped': '0',
                           'errors': '0',
                           'overruns': '0',
                           'packets': '0'}},
        'CONTENT': [u'UP BROADCAST RUNNING NOARP  MTU:1500  Metric:1',
                    u'collisions:0 txqueuelen:32'],
        'IPV4': [{}],
        'IPV6': [{}],
        'LINK': [{'ENCAP': u'Ethernet',
                  'MAC': u'c2:e8:cd:86:73:2b'}]},
    u'lo': {
        'RX': {'bytes': {'bytes_raw': '10427526'},
               'packets': {'dropped': '0',
                           'errors': '0',
                           'frame': '0',
                           'overruns': '0',
                           'packets': '9385'}},
        'TX': {'bytes': {'bytes_raw': '10427526'},
               'packets': {'carrier': '0',
                           'dropped': '0',
                           'errors': '0',
                           'overruns': '0',
                           'packets': '9385'}},
        'CONTENT': [u'inet addr:127.0.0.1  Mask:255.0.0.0',
                    u'inet6 addr: ::1/128 Scope:Host',
                    u'UP LOOPBACK RUNNING  MTU:65536  Metric:1',
                    u'collisions:0 txqueuelen:0'],
        'IPV4': [{'IP': u'127.0.0.1', 'MASK': u'255.0.0.0'}],
        'IPV6': [{'IP': u'::1', 'MASK': u'128', 'SCOPE': u'Host'}],
        'LINK': [{}]},
    u'pan0': {
        'RX': {'bytes': {'bytes_raw': '0'},
               'packets': {'dropped': '0',
                           'errors': '0',
                           'frame': '0',
                           'overruns': '0',
                           'packets': '0'}},
        'TX': {'bytes': {'bytes_raw': '0'},
               'packets': {'carrier': '0',
                           'dropped': '0',
                           'errors': '0',
                           'overruns': '0',
                           'packets': '0'}},
        'CONTENT': [u'inet addr:192.168.255.245  Bcast:192.168.255.247  Mask:255.255.255.248',
                    u'UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1',
                    u'collisions:0 txqueuelen:0'],
        'IPV4': [{'BRD': u'192.168.255.247',
                  'IP': u'192.168.255.245',
                  'MASK': u'255.255.255.248'}],
        'IPV6': [{}],
        'LINK': [{'ENCAP': u'Ethernet',
                  'MAC': u'82:1b:5b:02:c9:dc'}]},
    u'pan0:1': {'CONTENT': [u'inet addr:192.168.255.241  Bcast:192.168.255.247  Mask:255.255.255.248',
                            u'UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1'],
                'IPV4': [{'BRD': u'192.168.255.247',
                          'IP': u'192.168.255.241',
                          'MASK': u'255.255.255.248'}],
                'IPV6': [{}],
                'LINK': [{'ENCAP': u'Ethernet',
                          'MAC': u'82:1b:5b:02:c9:dc'}]},
    u'pan0:2': {'CONTENT': [u'inet addr:192.168.255.242  Bcast:192.168.255.247  Mask:255.255.255.248',
                            u'UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1'],
                'IPV4': [{'BRD': u'192.168.255.247',
                          'IP': u'192.168.255.242',
                          'MASK': u'255.255.255.248'}],
                'IPV6': [{}],
                'LINK': [{'ENCAP': u'Ethernet',
                          'MAC': u'82:1b:5b:02:c9:dc'}]}}
