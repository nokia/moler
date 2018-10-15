# -*- coding: utf-8 -*-
"""
ifconfig command module.
"""

__author__ = 'Sylwester Golonka'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'sylwester.golonka@nokia.com'

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
COMMAND_RESULT = {u'br0': {'CONTENT': [u'inet addr:10.0.0.64  Bcast:10.0.0.255  Mask:255.255.255.0',
                                       u'inet addr:10.0.0.65  Bcast:10.0.0.255  Mask:255.255.255.0',
                                       u'inet6 addr: fe80::a00:27ff:fe30:a67e/64 Scope:Link',
                                       u'UP BROADCAST RUNNING ALLMULTI  MTU:1500  Metric:1',
                                       u'RX packets:3625 errors:0 dropped:0 overruns:0 frame:0',
                                       u'TX packets:18083 errors:0 dropped:0 overruns:0 carrier:0',
                                       u'collisions:0 txqueuelen:0',
                                       u'RX bytes:630550 (615.7 KiB)  TX bytes:2560834 (2.4 MiB)'],
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
                      'CONTENT': [u'inet addr:192.168.255.61  Bcast:192.168.255.63  Mask:255.255.255.252',
                                  u'UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1',
                                  u'RX packets:0 errors:0 dropped:0 overruns:0 frame:0',
                                  u'TX packets:6 errors:0 dropped:0 overruns:0 carrier:0',
                                  u'collisions:0 txqueuelen:0',
                                  u'RX bytes:0 (0.0 B)  TX bytes:468 (468.0 B)'],
                      'IPV4': [{'BRD': u'192.168.255.63',
                                'IP': u'192.168.255.61',
                                'MASK': u'255.255.255.252'}],
                      'IPV6': [{}],
                      'LINK': [{'ENCAP': u'Ethernet',
                                'MAC': u'fe:4f:f5:ca:67:ec'}]},
                  u'eth0': {'CONTENT': [u'UP BROADCAST RUNNING ALLMULTI MULTICAST  MTU:1500  Metric:1',
                                        u'RX packets:3111 errors:0 dropped:0 overruns:0 frame:0',
                                        u'TX packets:18597 errors:0 dropped:0 overruns:0 carrier:0',
                                        u'collisions:0 txqueuelen:1000',
                                        u'RX bytes:378560 (369.6 KiB)  TX bytes:2863574 (2.7 MiB)'],
                            'IPV4': [{}],
                            'IPV6': [{}],
                            'LINK': [{'ENCAP': u'Ethernet',
                                      'MAC': u'60:a8:fe:74:f8:a9'}]},
                  u'eth1': {'CONTENT': [u'inet addr:192.168.255.129  Bcast:192.168.255.255  Mask:255.255.255.0',
                                        u'UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1',
                                        u'RX packets:2447 errors:0 dropped:0 overruns:0 frame:0',
                                        u'TX packets:47164 errors:0 dropped:0 overruns:0 carrier:0',
                                        u'collisions:0 txqueuelen:1000',
                                        u'RX bytes:344845 (336.7 KiB)  TX bytes:44222585 (42.1 MiB)'],
                            'IPV4': [{'BRD': u'192.168.255.255',
                                      'IP': u'192.168.255.129',
                                      'MASK': u'255.255.255.0'}],
                            'IPV6': [{}],
                            'LINK': [{'ENCAP': u'Ethernet',
                                      'MAC': u'b4:99:4c:b7:11:ab'}]},
                  u'eth1:2': {'CONTENT': [u'inet addr:192.168.255.1  Bcast:0.0.0.0  Mask:255.255.254.0',
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
                  u'eth3': {'CONTENT': [u'UP BROADCAST RUNNING ALLMULTI MULTICAST  MTU:1500  Metric:1',
                                        u'RX packets:514 errors:0 dropped:0 overruns:0 frame:0',
                                        u'TX packets:8 errors:0 dropped:0 overruns:0 carrier:0',
                                        u'collisions:0 txqueuelen:1000',
                                        u'RX bytes:302740 (295.6 KiB)  TX bytes:1799 (1.7 KiB)'],
                            'IPV4': [{}],
                            'IPV6': [{}],
                            'LINK': [{'ENCAP': u'Ethernet',
                                      'MAC': u'60:a8:fe:74:f8:aa'}]},
                  u'ifb0': {'CONTENT': [u'UP BROADCAST RUNNING NOARP  MTU:1500  Metric:1',
                                        u'RX packets:0 errors:0 dropped:0 overruns:0 frame:0',
                                        u'TX packets:0 errors:0 dropped:0 overruns:0 carrier:0',
                                        u'collisions:0 txqueuelen:32',
                                        u'RX bytes:0 (0.0 B)  TX bytes:0 (0.0 B)'],
                            'IPV4': [{}],
                            'IPV6': [{}],
                            'LINK': [{'ENCAP': u'Ethernet',
                                      'MAC': u'c2:e8:cd:86:73:2b'}]},
                  u'lo': {'CONTENT': [u'inet addr:127.0.0.1  Mask:255.0.0.0',
                                      u'inet6 addr: ::1/128 Scope:Host',
                                      u'UP LOOPBACK RUNNING  MTU:65536  Metric:1',
                                      u'RX packets:9385 errors:0 dropped:0 overruns:0 frame:0',
                                      u'TX packets:9385 errors:0 dropped:0 overruns:0 carrier:0',
                                      u'collisions:0 txqueuelen:0',
                                      u'RX bytes:10427526 (9.9 MiB)  TX bytes:10427526 (9.9 MiB)'],
                          'IPV4': [{'IP': u'127.0.0.1', 'MASK': u'255.0.0.0'}],
                          'IPV6': [{'IP': u'::1', 'MASK': u'128', 'SCOPE': u'Host'}],
                          'LINK': [{}]},
                  u'pan0': {'CONTENT': [u'inet addr:192.168.255.245  Bcast:192.168.255.247  Mask:255.255.255.248',
                                        u'UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1',
                                        u'RX packets:0 errors:0 dropped:0 overruns:0 frame:0',
                                        u'TX packets:0 errors:0 dropped:0 overruns:0 carrier:0',
                                        u'collisions:0 txqueuelen:0',
                                        u'RX bytes:0 (0.0 B)  TX bytes:0 (0.0 B)'],
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
