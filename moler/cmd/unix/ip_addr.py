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
    _re_interface = re.compile(r"^\d+:\s([a-z\d\.]+):.*$")
    _re_inet_v4 = re.compile(r"\s*inet\s+(\d+\.\d+\.\d+\.\d+)\/(\d+)\s(brd)\s(\d+\.\d+\.\d+\.\d+)\sscope\s(\S.*\S)\s(\S.*\S)")
    _re_inet_v4_no_br = re.compile(r"^\s*inet\s+(\d+\.\d+\.\d+\.\d+)\/(\d+)\sscope\s(\S.*\S)\s(\S.*\S)$")
    _re_inet_v6 = re.compile(r"^.*inet6\s(.*)\sscope\s(\S.*\S)\s?$")
    _re_link = re.compile(r"^.*(link\/.*)\s(.*)\s(brd)\s(\S.*\S)\s?$")
    def __init__(self, connection, prompt=None, new_line_chars=None, options=None):
        super(IpAddr, self).__init__(connection, prompt, new_line_chars)
        self._converter_helper = ConverterHelper()
        # Parameters defined by calling the command
        self.options = options
        self.matched = 0

    def build_command_string(self):
        cmd = "ip addr"
        if self.options:
            cmd = cmd + " " + self.options
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_interface(line)
                self._parse_inet_v4(line)
                self._parse_inet_v4_no_br(line)
                self._parse_inet_v6(line)
                self._parse_link(line)
            except ParsingDone:
                pass
        return super(IpAddr, self).on_new_line(line, is_full_line)


    def _parse_interface(self, line):
        if self._regex_helper.search_compiled(IpAddr._re_interface, line):
            self.if_name = self._regex_helper.group(1)
            if self.if_name not in self.current_ret:
                self.current_ret[self.if_name] = dict()



    def _parse_inet_v4(self, line):
        if self._regex_helper.search_compiled(IpAddr._re_inet_v4, line):
            try:
                isinstance(self.current_ret[self.if_name]["arr"], list)
            except:
                self.current_ret[self.if_name]["arr"] = []
            self.current_ret[self.if_name]["arr"].append({"ip4":self._regex_helper.group(1), "mask":self._regex_helper.group(2)})
            scope = self._regex_helper.group(5) + " " + self._regex_helper.group(6)
            self.current_ret[self.if_name][scope] = self._regex_helper.group(1)
            self.current_ret[self.if_name][scope + " " + self._regex_helper.group(3)] = self._regex_helper.group(4)
            self.current_ret[self.if_name][scope + " mask"] = self._regex_helper.group(2)

    def _parse_inet_v4_no_br(self, line):
        if self._regex_helper.search_compiled(IpAddr._re_inet_v4_no_br, line):
            try:
                isinstance(self.current_ret[self.if_name]["arr"], list)
            except:
                self.current_ret[self.if_name]["arr"] = []
            self.current_ret[self.if_name]["arr"].append(
                {"ip4": self._regex_helper.group(1), "mask": self._regex_helper.group(2)})
            scope = self._regex_helper.group(3) + " " + self._regex_helper.group(4)
            self.current_ret[self.if_name][scope] = self._regex_helper.group(1)
            self.current_ret[self.if_name][scope + " mask"] = self._regex_helper.group(2)
    def _parse_inet_v6(self, line):
        if self._regex_helper.search_compiled(IpAddr._re_inet_v6, line):
            self.current_ret[self.if_name][self._regex_helper.group(2)] = self._regex_helper.group(1)
    def _parse_link(self, line):
        if self._regex_helper.search_compiled(IpAddr._re_link, line):
            self.current_ret[self.if_name][self._regex_helper.group(1)] = self._regex_helper.group(2)
            self.current_ret[self.if_name][self._regex_helper.group(1)+self._regex_helper.group(3)] = self._regex_helper.group(4)


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
    'br4': {   },
    'eth0': {   },
    'eth1': {   },
    'eth2': {   },
    'eth3': {   },
    'lo': {   },
    'vboxnet0': {   }
}
