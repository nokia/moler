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
    def __init__(self, connection, prompt=None, new_line_chars=None, options=None):
        super(IpAddr, self).__init__(connection, prompt, new_line_chars)
        self._converter_helper = ConverterHelper()
        # Parameters defined by calling the command
        self.if_name = None
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
                self._parse_v4_brd(line)
                self._parse_v6(line)
                self._parse_link(line)
            except ParsingDone:
                pass
        return super(IpAddr, self).on_new_line(line, is_full_line)

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

    _re_interface = re.compile(r"^\d+:\s(?P<INTERFACE>[a-z\d.]+):.*$")

    def _parse_interface(self, line):
        if self._regex_helper.search_compiled(IpAddr._re_interface, line):
            self.current_ret[self._regex_helper.group("INTERFACE")] = {"IPV4": [{}], "IPV6": [{}], "LINK": [{}]}
            self.if_name = self._regex_helper.group("INTERFACE")

    _re_ip_v4_brd = re.compile(
        r"\s*inet\s+(?P<IP>\d+\.\d+\.\d+\.\d+)\/(?P<MASK>\d+)\s(brd)\s(?P<BRD>\d+\.\d+\.\d+\.\d+)\sscope\s(\S.*\S)\s(\S.*\S)")
    _key_ip_v4_brd = ["IP", "MASK", "BRD"]

    def _parse_v4_brd(self, line):
        return self._process_line(line, IpAddr._re_ip_v4_brd, IpAddr._key_ip_v4_brd, "IPV4")

    _re_ip_v4 = re.compile(r"^\s*inet\s+(?P<IP>\d+\.\d+\.\d+\.\d+)\/(?P<MASK>\d+)\sscope\s(\S.*\S)\s(\S.*\S)$")
    _key_ip_v4 = ["IP", "MASK"]

    def _parse_v4(self, line):
        return self._process_line(line, IpAddr._re_ip_v4, IpAddr._key_ip_v4, "IPV4")

    _re_ip_v6 = re.compile(r"^.*inet6\s(?P<IP>.*)\/(?P<MASK>\d+)\sscope\s(\S.*\S)\s?$")

    _key_ip_v6 = ["IP", "MASK"]

    def _parse_v6(self, line):
        return self._process_line(line, IpAddr._re_ip_v6, IpAddr._key_ip_v6, "IPV6")

    _re_link = re.compile(r"^.*(link/[a-z]*)\s(?P<MAC>.*)\sbrd\s(?P<BRD>.*)$")
    _key_link = ["MAC", "BRD"]

    def _parse_link(self, line):
        return self._process_line(line, IpAddr._re_link, IpAddr._key_link, "LINK")


COMMAND_OUTPUT = """
 root@fzm-lsp-k2:~# ip addr show
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdiscd noqueue state UNKNOWN group default
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
COMMAND_RESULT = {
    'eth0': {
        'IPV4': [{
            'BRD': '10.83.207.255',
            'IP': '10.83.206.42',
            'MASK': '21'}],
        'IPV6': [{
            'IP': 'fe80::216:3eff:fe71:7b5d',
            'MASK': '64'}],
        'LINK': [{
            'BRD': 'ff:ff:ff:ff:ff:ff',
            'MAC': '00:16:3e:71:7b:5d'}]},
    'eth1': {
        'IPV4': [{
            'IP': '192.168.255.126',
            'MASK': '24'}, {
            'IP': '10.0.0.3',
            'MASK': '24'}],
        'IPV6': [{
            'IP': 'fe80::216:3eff:fe86:4a3a',
            'MASK': '64'}],
        'LINK': [
            {
                'BRD': 'ff:ff:ff:ff:ff:ff',
                'MAC': '00:16:3e:86:4a:3a'}]},
    'eth2': {
        'IPV4': [{
            'BRD': '192.168.255.255',
            'IP': '192.168.255.25',
            'MASK': '24'}],
        'IPV6': [{
            'IP': 'fe80::216:3eff:fe04:3515',
            'MASK': '64'}],
        'LINK': [{
            'BRD': 'ff:ff:ff:ff:ff:ff',
            'MAC': '00:16:3e:04:35:15'}]},
    'eth3': {
        'IPV4': [{}],
        'IPV6': [{}],
        'LINK': [{
            'BRD': 'ff:ff:ff:ff:ff:ff',
            'MAC': '00:16:3e:04:35:15'}]},
    'lo': {
        'IPV4': [{
            'IP': '127.0.0.1',
            'MASK': '8'}],
        'IPV6': [{
            'IP': '::1',
            'MASK': '128'}],
        'LINK': [{
            'BRD': '00:00:00:00:00:00',
            'MAC': '00:00:00:00:00:00'}]}}
