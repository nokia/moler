# -*- coding: utf-8 -*-
"""
ip addr command module.
"""

__author__ = 'Sylwester Golonka'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'sylwester.golonka@nokia.com'

import re

from moler.cmd.unix.genericunix import GenericUnix
from moler.cmd.converterhelper import ConverterHelper
from moler.exceptions import ParsingDone



class IpAddr(GenericUnix):
    _re_inet_v4_no_br = re.compile(r"^\s*inet\s+(\d+\.\d+\.\d+\.\d+)\/(\d+)\sscope\s(\S.*\S)\s(\S.*\S)$")
    _re_inet_v6 = re.compile(r"^.*inet6\s(.*)\sscope\s(\S.*\S)\s?$")
    _re_link = re.compile(r"^.*(link\/.*)\s(.*)\s(brd)\s(\S.*\S)\s?$")
    def __init__(self, connection, prompt=None, new_line_chars=None, options=None):
        super(IpAddr, self).__init__(connection, prompt, new_line_chars)
        self._converter_helper = ConverterHelper()
        # Parameters defined by calling the command
        self.options = options

    def build_command_string(self):
        cmd = "ip addr"
        if self.options:
            cmd = cmd + " " + self.options
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_interface(line)
                self._parse_v4(line)
            except ParsingDone:
                pass
        return super(IpAddr, self).on_new_line(line, is_full_line)

    def _process_line(self, line, regexp, key_list, type):
        if self._regex_helper.search_compiled(regexp, line):
            _ret = dict()
            for key in key_list:
                if type=="INTERFACE":
                    self.current_ret[self._regex_helper.group(key)] = {"IPv4":[], "IPv6":[], "link":[]}
                    self.if_name = self._regex_helper.group(key)
                _ret[key] = self._regex_helper.group(key)
            if not type=="INTERFACE":
                self.current_ret[self.if_name][type].append(_ret)
            raise ParsingDone

    _re_interface = re.compile(r"^\d+:\s(?P<INTERFACE>[a-z\d\.]+):.*$")
    _key_interface = ["INTERFACE"]
    def _parse_interface(self, line):
        return self._process_line(line, IpAddr._re_interface, IpAddr._key_interface, "INTERFACE")

    _re_inet_v4 = re.compile(
            r"\s*inet\s+(?P<IP>\d+\.\d+\.\d+\.\d+)\/(?P<MASK>\d+)\s(brd)\s(\d+\.\d+\.\d+\.\d+)\sscope\s(\S.*\S)\s(\S.*\S)")

    _key_v4 = ["IP", "MASK"]
    def _parse_v4(self, line):
        return self._process_line(line, IpAddr._re_inet_v4, IpAddr._key_v4, "IPv4")

COMMAND_OUTPUT = """
 root@fzm-lsp-k2:~# ip addr show
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default 
      link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
      inet 127.0.0.1/8 scope host lo
         valid_lft forever preferred_lft forever
      inet6 ::1/128 scope host 
         valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UNKNOWN group default qlen 1000
      link/ether 00:16:3e:71:7b:5d brd ff:ff:ff:ff:ff:ff
      inet 10.83.206.42/21 brd 10.83.207.255 scope global eth0
      inet 10.00.00.11/24 brd 10.83.207.255 scope global eth0
         valid_lft forever preferred_lft forever
      inet6 fe80::216:3eff:fe71:7b5d/64 scope link 
         valid_lft forever preferred_lft forever
3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1600 qdisc pfifo_fast state UNKNOWN group default qlen 5000
      link/ether 00:16:3e:86:4a:3a brd ff:ff:ff:ff:ff:ff
      inet 192.168.255.126/24 scope global eth1
         valid_lft forever preferred_lft forever
      inet 10.0.0.3/24 scope global eth1
         valid_lft forever preferred_lft forever
      inet6 fe80::216:3eff:fe86:4a3a/64 scope link 
         valid_lft forever preferred_lft forever
4: eth2: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UNKNOWN group default qlen 1000
      link/ether 00:16:3e:04:35:15 brd ff:ff:ff:ff:ff:ff
      inet 192.168.255.25/24 brd 192.168.255.255 scope global eth2
         valid_lft forever preferred_lft forever
      inet6 fe80::216:3eff:fe04:3515/64 scope link 
         valid_lft forever preferred_lft forever
5: eth3: <BROADCAST,MULTICAST> mtu 1500 qdisc noop state DOWN group default qlen 1000
      link/ether 00:16:3e:04:35:15 brd ff:ff:ff:ff:ff:ff
  root@fzm-lsp-k2:~# """
COMMAND_KWARGS = {}
COMMAND_RESULT ={
   'eth0': {   'arr': [
                            {
                                'ip4': '10.83.206.42',
                                'mask': '21'
                            }
                        ],
                 'global eth0': '10.83.206.42',
                 'global eth0 brd': '10.83.207.255',
                 'global eth0 mask': '21',
                 'link': 'fe80::216:3eff:fe71:7b5d/64',
                 'link/ether': '00:16:3e:71:7b:5d',
                 'link/etherbrd': 'ff:ff:ff:ff:ff:ff'},
    'eth1': {   'arr': [
                            {
                                'ip4': '192.168.255.126',
                                'mask': '24'
                            },
                            {   'ip4': '10.0.0.3',
                                'mask': '24'
                            }
                        ],
                 'global eth1': '10.0.0.3',
                 'global eth1 mask': '24',
                 'link': 'fe80::216:3eff:fe86:4a3a/64',
                 'link/ether': '00:16:3e:86:4a:3a',
                 'link/etherbrd': 'ff:ff:ff:ff:ff:ff'},
    'eth2': {   'arr': [
                            {   'ip4': '192.168.255.25',
                                'mask': '24'
                            }
                        ],
                 'global eth2': '192.168.255.25',
                 'global eth2 brd': '192.168.255.255',
                 'global eth2 mask': '24',
                 'link': 'fe80::216:3eff:fe04:3515/64',
                 'link/ether': '00:16:3e:04:35:15',
                 'link/etherbrd': 'ff:ff:ff:ff:ff:ff'},
    'eth3': {   'link/ether': '00:16:3e:04:35:15',
                 'link/etherbrd': 'ff:ff:ff:ff:ff:ff'},
    'lo': {   'arr': [
                            {
                                'ip4': '127.0.0.1',
                                'mask': '8'
                            }
                    ],
               'host': '::1/128',
               'host lo': '127.0.0.1',
               'host lo mask': '8',
               'link/loopback': '00:00:00:00:00:00',
               'link/loopbackbrd': '00:00:00:00:00:00'}}
