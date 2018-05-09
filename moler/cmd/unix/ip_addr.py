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
            self.current_ret[self.if_name]["ipv4"] = self._regex_helper.group(1)
            self.current_ret[self.if_name]["mask"] = self._regex_helper.group(2)
            #dodac reszte parametow


COMMAND_OUTPUT = """
ute@debdev:~$ ip addr
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default 
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
2: eth2: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
    link/ether 40:a8:f0:60:8d:09 brd ff:ff:ff:ff:ff:ff
    inet6 fe80::42a8:f0ff:fe60:8d09/64 scope link 
       valid_lft forever preferred_lft forever
3: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
    link/ether 68:05:ca:18:7c:d3 brd ff:ff:ff:ff:ff:ff
    inet 10.83.204.15/21 brd 10.83.207.255 scope global eth0
       valid_lft forever preferred_lft forever
    inet6 fe80::6a05:caff:fe18:7cd3/64 scope link 
       valid_lft forever preferred_lft forever
4: eth3: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
    link/ether 68:05:ca:10:bb:82 brd ff:ff:ff:ff:ff:ff
    inet6 fe80::6a05:caff:fe10:bb82/64 scope link 
       valid_lft forever preferred_lft forever
5: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
    link/ether 68:05:ca:18:71:f6 brd ff:ff:ff:ff:ff:ff
    inet 192.168.255.100/24 scope global eth1
       valid_lft forever preferred_lft forever
    inet6 fe80::6a05:caff:fe18:71f6/64 scope link 
       valid_lft forever preferred_lft forever
6: br4: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UNKNOWN group default 
    link/ether 8a:57:24:5f:a7:2d brd ff:ff:ff:ff:ff:ff
    inet 172.16.2.2/24 brd 172.16.2.255 scope global br4
       valid_lft forever preferred_lft forever
    inet6 fe80::8857:24ff:fe5f:a72d/64 scope link 
       valid_lft forever preferred_lft forever
7: vboxnet0: <BROADCAST,MULTICAST> mtu 1500 qdisc noop state DOWN group default qlen 1000
    link/ether 0a:00:27:00:00:00 brd ff:ff:ff:ff:ff:ff
ute@debdev:~$"""
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
