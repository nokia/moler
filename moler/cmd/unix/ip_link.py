# -*- coding: utf-8 -*-
"""
Ip link command module.
"""

__author__ = 'Julia Patacz'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'julia.patacz@nokia.com'

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone


class IpLink(GenericUnixCommand):
    def __init__(self, connection, action, prompt=None, newline_chars=None, options=None, runner=None):
        super(IpLink, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.ret_required = False
        self.action = action
        self.options = options
        self.line = False

    def build_command_string(self):
        cmd = "ip link {}".format(self.action)
        if self.options:
            cmd = "{} {}".format(cmd, self.options)
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_line_brd(line)
                self._parse_line_int_trans_mtu_qdisc_state_mode_group_qlen(line)
                self._parse_line_int_trans_mtu_qdisc_state_mode_group(line)
            except ParsingDone:
                pass
        return super(IpLink, self).on_new_line(line, is_full_line)

    # link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    _re_link_brd = re.compile(
        r"(?P<LINK>\S+)\s+(?P<VAL>\S+:\S+:\S+:\S+:\S+:\S+)\s+(?P<KEY>\S+)\s+(?P<VAL_2>\S+:\S+:\S+:\S+:\S+:\S+)")

    def _parse_line_brd(self, line):
        if self.line and self._regex_helper.search_compiled(IpLink._re_link_brd, line):
            temp_link = self._regex_helper.group('LINK')
            temp_val = self._regex_helper.group('VAL')
            temp_brd = self._regex_helper.group('KEY')
            temp_val_2 = self._regex_helper.group('VAL_2')

            self.current_ret[self.line][temp_link] = temp_val
            self.current_ret[self.line][temp_brd] = temp_val_2

            self.line = False

            raise ParsingDone

    # 2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
    _re_line_int_trans_mtu_qdisc_state_mode_group_qlen = re.compile(
        r"(?P<LINE>\d+):\s+(?P<INT>\S+):\s+(?P<TRANS>\S+)\s+mtu\s+(?P<MTU>\S+)\s+qdisc\s+(?P<QDISC>\S+)\s+state\s+(?P<STATE>\S+)\s+mode\s+(?P<MODE>\S+)\s+group\s+(?P<GROUP>\S+)\s+qlen\s+(?P<QLEN>\S+)")

    def _parse_line_int_trans_mtu_qdisc_state_mode_group_qlen(self, line):
        if self._regex_helper.search_compiled(IpLink._re_line_int_trans_mtu_qdisc_state_mode_group_qlen, line):
            temp_line = self._regex_helper.group('LINE')
            temp_int = self._regex_helper.group('INT')
            temp_trans = self._regex_helper.group('TRANS')
            temp_mtu = self._regex_helper.group('MTU')
            temp_qdisc = self._regex_helper.group('QDISC')
            temp_state = self._regex_helper.group('STATE')
            temp_mode = self._regex_helper.group('MODE')
            temp_group = self._regex_helper.group('GROUP')
            temp_qlen = self._regex_helper.group('QLEN')

            if temp_line not in self.current_ret.keys():
                self.current_ret[temp_line] = {}
            self.current_ret[temp_line]['interface'] = temp_int
            self.current_ret[temp_line]['transmission'] = temp_trans
            self.current_ret[temp_line]['mtu'] = temp_mtu
            self.current_ret[temp_line]['qdisc'] = temp_qdisc
            self.current_ret[temp_line]['state'] = temp_state
            self.current_ret[temp_line]['mode'] = temp_mode
            self.current_ret[temp_line]['group'] = temp_group
            self.current_ret[temp_line]['qlen'] = temp_qlen

            self.line = temp_line

            raise ParsingDone

    # 1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default
    _re_line_int_trans_mtu_qdisc_state_mode_group = re.compile(
        r"(?P<LINE>\d+):\s+(?P<INT>\S+):\s+(?P<TRANS>\S+)\s+mtu\s+(?P<MTU>\S+)\s+qdisc\s+(?P<QDISC>\S+)\s+state\s+(?P<STATE>\S+)\s+mode\s+(?P<MODE>\S+)\s+group\s+(?P<GROUP>\S+)")

    def _parse_line_int_trans_mtu_qdisc_state_mode_group(self, line):
        if self._regex_helper.search_compiled(IpLink._re_line_int_trans_mtu_qdisc_state_mode_group, line):
            temp_line = self._regex_helper.group('LINE')
            temp_int = self._regex_helper.group('INT')
            temp_trans = self._regex_helper.group('TRANS')
            temp_mtu = self._regex_helper.group('MTU')
            temp_qdisc = self._regex_helper.group('QDISC')
            temp_state = self._regex_helper.group('STATE')
            temp_mode = self._regex_helper.group('MODE')
            temp_group = self._regex_helper.group('GROUP')

            if temp_line not in self.current_ret.keys():
                self.current_ret[temp_line] = {}
            self.current_ret[temp_line]['interface'] = temp_int
            self.current_ret[temp_line]['transmission'] = temp_trans
            self.current_ret[temp_line]['mtu'] = temp_mtu
            self.current_ret[temp_line]['qdisc'] = temp_qdisc
            self.current_ret[temp_line]['state'] = temp_state
            self.current_ret[temp_line]['mode'] = temp_mode
            self.current_ret[temp_line]['group'] = temp_group

            self.line = temp_line


COMMAND_OUTPUT = """
host:~ # ip link show
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
    link/ether 08:00:27:05:ae:4d brd ff:ff:ff:ff:ff:ff
host:~ # """
COMMAND_KWARGS = {'action': 'show'}
COMMAND_RESULT = {
    '1': {'group': 'default',
          'interface': 'lo',
          'mode': 'DEFAULT',
          'mtu': '65536',
          'qdisc': 'noqueue',
          'state': 'UNKNOWN',
          'transmission': '<LOOPBACK,UP,LOWER_UP>',
          'link/loopback': '00:00:00:00:00:00',
          'brd': '00:00:00:00:00:00',
          },
    '2': {'group': 'default',
          'interface': 'eth0',
          'mode': 'DEFAULT',
          'mtu': '1500',
          'qdisc': 'pfifo_fast',
          'state': 'UP',
          'transmission': '<BROADCAST,MULTICAST,UP,LOWER_UP>',
          'qlen': '1000',
          'link/ether': '08:00:27:05:ae:4d',
          'brd': 'ff:ff:ff:ff:ff:ff',
          }
}
