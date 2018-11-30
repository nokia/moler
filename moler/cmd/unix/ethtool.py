# -*- coding: utf-8 -*-
"""
Ethtool command module.
"""

__author__ = 'Julia Patacz'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'julia.patacz@nokia.com'

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone


class Ethtool(GenericUnixCommand):

    def __init__(self, connection, interface, prompt=None, newline_chars=None, options=None, runner=None):
        super(Ethtool, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                      runner=runner)
        self.interface = interface
        self.options = options
        self.ret_required = False

        self.int = None
        self.key = None
        self._arr_name = None
        self._curr_msg_lvl = None

    def build_command_string(self):
        if self.options:
            cmd = "ethtool {} {}".format(self.options, self.interface)
        else:
            cmd = "ethtool {}".format(self.interface)
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_int(line)
                self._parse_arr_name(line)
                self._parse_key_value(line)
                self._parse_value_arr(line)
                self._parse_curr_msg_lvl(line)
                self._parse_key(line)
                self._parse_param_mode(line)

            except ParsingDone:
                pass
        return super(Ethtool, self).on_new_line(line, is_full_line)

    # Settings for eth0:
    _re_int = re.compile(r"(Settings for|Time stamping parameters for)\s+(?P<INT>\S+):")

    def _parse_int(self, line):
        if self._regex_helper.search_compiled(Ethtool._re_int, line):
            self.int = self._regex_helper.group('INT')
            if self.int not in self.current_ret.keys():
                self.current_ret[self.int] = {}
            raise ParsingDone

    # Capabilities:
    _re_key = re.compile(r"(?P<KEY>\S.*\S):")

    def _parse_key(self, line):
        if self._regex_helper.search_compiled(Ethtool._re_key, line):
            self.key = self._regex_helper.group('KEY')
            if self.key not in self.current_ret[self.int].keys():
                self.current_ret[self.int][self.key] = {}
            raise ParsingDone

    # Supported link modes:   10baseT/Half 10baseT/Full
    _re_arr_name = re.compile(r"^\s+(?P<ARR_NAME>.*\s+modes):\s*(?P<VALUE>\S.*\S)\s*$")

    def _parse_arr_name(self, line):
        if self.int and self._regex_helper.search_compiled(Ethtool._re_arr_name, line):
            self._arr_name = self._regex_helper.group('ARR_NAME')
            if self._arr_name not in self.current_ret[self.int].keys():
                self.current_ret[self.int][self._arr_name] = []
            self.current_ret[self.int][self._arr_name].append(self._regex_helper.group('VALUE'))
            raise ParsingDone

    # 100baseT/Half 100baseT/Full
    _re_value_arr = re.compile(r"^\s+(?P<VALUE>\S.*\S|\S)\s*$")

    def _parse_value_arr(self, line):
        if self.int and self._arr_name and self._regex_helper.search_compiled(Ethtool._re_value_arr, line):
            self.current_ret[self.int][self._arr_name].append(self._regex_helper.group('VALUE'))
            raise ParsingDone

    # Supports auto-negotiation: Yes
    _re_key_value = re.compile(r"(?P<KEY>\S.*\S|\S)\s*:\s*(?P<VALUE>\S.*\S|\S)\s*$")

    def _parse_key_value(self, line):
        if self.int and self._regex_helper.search_compiled(Ethtool._re_key_value, line):
            if self._regex_helper.group('KEY') == 'Current message level':
                self._curr_msg_lvl = self._regex_helper.group('KEY')
            self.current_ret[self.int][self._regex_helper.group('KEY')] = self._regex_helper.group('VALUE')
            self._arr_name = None
            raise ParsingDone

    #     hardware-transmit     (SOF_TIMESTAMPING_TX_HARDWARE)
    _re_param_mode = re.compile(r"^\s+(?P<PARAM>\S+)\s+(?P<MODE>\S+)$")

    def _parse_param_mode(self, line):
        if self.key and self._regex_helper.search_compiled(Ethtool._re_param_mode, line):
            self.current_ret[self.int][self.key][self._regex_helper.group('PARAM')] = self._regex_helper.group('MODE')
            raise ParsingDone

    # drv probe link timer ifdown ifup rx_err tx_err tx_queued intr tx_done rx_status pktdata hw wol
    _re_curr_msg_lvl = re.compile(r"^\s+[\w+\s+]+$")

    def _parse_curr_msg_lvl(self, line):
        if self._curr_msg_lvl and self._regex_helper.search_compiled(Ethtool._re_curr_msg_lvl, line):
            self.current_ret[self.int][self._curr_msg_lvl] = "{} {}".format(
                self.current_ret[self.int][self._curr_msg_lvl], line.strip())
            self._curr_msg_lvl = None
            raise ParsingDone


COMMAND_OUTPUT = """
toor4nsn@fzm-lsp-k2:~# ethtool eth0
Settings for eth0:
    Supported ports: [ TP MII ]
    Supported link modes:   10baseT/Half 10baseT/Full
                            100baseT/Half 100baseT/Full
                            1000baseT/Half 1000baseT/Full
    Supported pause frame use: No
    Supports auto-negotiation: Yes
    Advertised link modes:  10baseT/Full
                            100baseT/Full
                            1000baseT/Full
    Advertised pause frame use: No
    Advertised auto-negotiation: Yes
    Link partner advertised link modes:  10baseT/Half 10baseT/Full
                                         100baseT/Half 100baseT/Full
                                         1000baseT/Full
    Link partner advertised pause frame use: Symmetric
    Link partner advertised auto-negotiation: Yes
    Speed: 1000Mb/s
    Duplex: Full
    Port: MII
    PHYAD: 0
    Transceiver: external
    Auto-negotiation: on
    Current message level: 0x00007fff (32767)
                   drv probe link timer ifdown ifup rx_err tx_err tx_queued intr tx_done rx_status pktdata hw wol
    Link detected: yes
toor4nsn@fzm-lsp-k2:~# """
COMMAND_KWARGS = {
    'interface': 'eth0'
}
COMMAND_RESULT = {
    'eth0': {
        'Advertised auto-negotiation': 'Yes',
        'Advertised link modes': ['10baseT/Full',
                                  '100baseT/Full',
                                  '1000baseT/Full'],
        'Advertised pause frame use': 'No',
        'Auto-negotiation': 'on',
        'Current message level': '0x00007fff (32767) drv probe link timer ifdown ifup rx_err tx_err tx_queued intr tx_done rx_status pktdata hw wol',
        'Duplex': 'Full',
        'Link detected': 'yes',
        'Link partner advertised auto-negotiation': 'Yes',
        'Link partner advertised link modes': [
            '10baseT/Half 10baseT/Full',
            '100baseT/Half 100baseT/Full',
            '1000baseT/Full'],
        'Link partner advertised pause frame use': 'Symmetric',
        'PHYAD': '0',
        'Port': 'MII',
        'Speed': '1000Mb/s',
        'Supported link modes': ['10baseT/Half 10baseT/Full',
                                 '100baseT/Half 100baseT/Full',
                                 '1000baseT/Half 1000baseT/Full'],
        'Supported pause frame use': 'No',
        'Supported ports': '[ TP MII ]',
        'Supports auto-negotiation': 'Yes',
        'Transceiver': 'external',
    },
}

COMMAND_OUTPUT_with_options = """toor4nsn@fzm-lsp-k2:~# ethtool -T eth0
Time stamping parameters for eth0:
Capabilities:
    hardware-transmit     (SOF_TIMESTAMPING_TX_HARDWARE)
    software-transmit     (SOF_TIMESTAMPING_TX_SOFTWARE)
    hardware-receive      (SOF_TIMESTAMPING_RX_HARDWARE)
    software-receive      (SOF_TIMESTAMPING_RX_SOFTWARE)
    software-system-clock (SOF_TIMESTAMPING_SOFTWARE)
    hardware-raw-clock    (SOF_TIMESTAMPING_RAW_HARDWARE)
PTP Hardware Clock: 1
Hardware Transmit Timestamp Modes:
    off                   (HWTSTAMP_TX_OFF)
    on                    (HWTSTAMP_TX_ON)
Hardware Receive Filter Modes:
    none                  (HWTSTAMP_FILTER_NONE)
    ptpv1-l4-event        (HWTSTAMP_FILTER_PTP_V1_L4_EVENT)
    ptpv2-event           (HWTSTAMP_FILTER_PTP_V2_EVENT)
toor4nsn@fzm-lsp-k2:~# """
COMMAND_KWARGS_with_options = {
    'interface': 'eth0',
    'options': '-T'
}
COMMAND_RESULT_with_options = {
    'eth0': {
        'PTP Hardware Clock': '1',
        'Capabilities': {
            'hardware-raw-clock': '(SOF_TIMESTAMPING_RAW_HARDWARE)',
            'hardware-receive': '(SOF_TIMESTAMPING_RX_HARDWARE)',
            'hardware-transmit': '(SOF_TIMESTAMPING_TX_HARDWARE)',
            'software-receive': '(SOF_TIMESTAMPING_RX_SOFTWARE)',
            'software-system-clock': '(SOF_TIMESTAMPING_SOFTWARE)',
            'software-transmit': '(SOF_TIMESTAMPING_TX_SOFTWARE)',
        },
        'Hardware Transmit Timestamp Modes': {
            'off': '(HWTSTAMP_TX_OFF)',
            'on': '(HWTSTAMP_TX_ON)',
        },
        'Hardware Receive Filter Modes': {
            'none': '(HWTSTAMP_FILTER_NONE)',
            'ptpv1-l4-event': '(HWTSTAMP_FILTER_PTP_V1_L4_EVENT)',
            'ptpv2-event': '(HWTSTAMP_FILTER_PTP_V2_EVENT)',
        },
    },
}
