# -*- coding: utf-8 -*-
"""
Hciconfig command module.
"""

__author__ = 'Sylwester Golonka'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'sylwester.golonka@nokia.com'

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone


class Hciconfig(GenericUnixCommand):
    def __init__(self, connection, options=None, prompt=None, newline_chars=None, runner=None):
        super(Hciconfig, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                        runner=runner)
        self.if_name = None
        self.options = options

    def build_command_string(self):
        cmd = "hciconfig"
        if self.options:
            cmd = cmd + " " + self.options
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_content(line)
                self._parse_interface(line)
                self._parse_bd_address(line)
                self._parse_RX_TX(line)
                self._parse_HCI_LMP(line)
                self._parse_details(line)
            except ParsingDone:
                pass
        return super(Hciconfig, self).on_new_line(line, is_full_line)

    _re_interface = re.compile(r"^(?P<INTERFACE>\S+):\s+Type:\s(?P<TYPE>.*)\s+Bus:\s+(?P<BUS>.*)$")

    def _parse_interface(self, line):
        if self._regex_helper.search_compiled(Hciconfig._re_interface, line):
            self.if_name = self._regex_helper.group("INTERFACE")
            self.current_ret[self.if_name] = dict()
            self.current_ret[self.if_name]['content'] = []
            self.current_ret[self.if_name]['content'].append(line)
            self.current_ret[self.if_name]["TYPE"] = self._regex_helper.group("TYPE")
            self.current_ret[self.if_name]["BUS"] = self._regex_helper.group("BUS")
            raise ParsingDone

    _re_content = re.compile(r'\s+(?P<VALUE>.*)')

    def _parse_content(self, line):
        if self.if_name:
            if self._regex_helper.search_compiled(Hciconfig._re_content, line):
                self.current_ret[self.if_name]["content"].append(self._regex_helper.group("VALUE"))

    _re_bd_address = re.compile(
        r"\s+(?P<BD_ADDRESS>\S+)\s+ACL MTU:\s+(?P<ACL_MTU>\S+)\s+SCO MTU:\s+(?P<SCO_MTU>\S+)")

    def _parse_bd_address(self, line):
        if self._regex_helper.search_compiled(Hciconfig._re_bd_address, line):
            self.current_ret[self.if_name]["BD_ADDRESS"] = self._regex_helper.group("BD_ADDRESS")
            self.current_ret[self.if_name]["ACL_MTU"] = self._regex_helper.group("ACL_MTU")
            self.current_ret[self.if_name]["SCO_MTU"] = self._regex_helper.group("SCO_MTU")
            raise ParsingDone

    _re_details = re.compile(r'\s+(?P<KEY>.*):\s+(?P<VALUE>.*)')

    def _parse_details(self, line):
        if self._regex_helper.search_compiled(Hciconfig._re_details, line):
            self.current_ret[self.if_name][self._regex_helper.group("KEY")] = self._regex_helper.group("VALUE")
            raise ParsingDone

    _re_RX_TX = re.compile(r'(?P<TYPE>RX|TX)')
    _re_RX_TX_details = re.compile(r'(?P<KEY>\w+):(?P<VALUE>\d+)')

    def _parse_RX_TX(self, line):
        if self._regex_helper.search_compiled(Hciconfig._re_RX_TX, line):
            type = self._regex_helper.group("TYPE")
            self.current_ret[self.if_name][type] = dict()
            parse = re.findall(Hciconfig._re_RX_TX_details, line)
            for key, value in parse:
                self.current_ret[self.if_name][type][key] = value
            raise ParsingDone

    _re_HCI_LMP = re.compile(r'\s+(?P<TYPE>.*)\s+Version:\s(?P<VERSION>.*)\s\s(?P<KEY>\w+):\s(?P<VALUE>\w+)')

    def _parse_HCI_LMP(self, line):
        if self._regex_helper.search_compiled(Hciconfig._re_HCI_LMP, line):
            type = self._regex_helper.group("TYPE")
            self.current_ret[self.if_name][type] = dict()
            self.current_ret[self.if_name][type]["VERSION"] = self._regex_helper.group("VERSION")
            self.current_ret[self.if_name][type][self._regex_helper.group("KEY")] = self._regex_helper.group("VALUE")
            raise ParsingDone


COMMAND_OUTPUT = """
toor4nsn@fzm-lsp-k2:~# hciconfig -a
hci0:   Type: BR/EDR  Bus: UART
        BD Address: 00:17:E9:21:E6:D9  ACL MTU: 1021:4  SCO MTU: 180:4
        UP RUNNING PSCAN ISCAN
        RX bytes:1267 acl:0 sco:0 events:71 errors:0
        TX bytes:2171 acl:0 sco:0 commands:71 errors:0
        Features: 0xff 0xfe 0x2d 0xfe 0xdb 0xff 0x7b 0x87
        Packet type: DM1 DM3 DM5 DH1 DH3 DH5 HV1 HV2 HV3
        Link policy: HOLD SNIFF
        Link mode: MASTER
        Name: 'FAE39B01'
        Class: 0x020000
        Service Classes: Networking
        Device Class: Miscellaneous,
        HCI Version: 4.0 (0x6)  Revision: 0x0
        LMP Version: 4.0 (0x6)  Subversion: 0x1b55
        Manufacturer: Texas Instruments Inc. (13)
toor4nsn@fzm-lsp-k2:~#
 """
COMMAND_KWARGS = {
    "options": "-a"
}

COMMAND_RESULT = {u'hci0': {'ACL_MTU': u'1021:4',
                            'BD_ADDRESS': u'00:17:E9:21:E6:D9',
                            'BUS': u'UART',
                            u'Class': u'0x020000',
                            u'Device Class': u'Miscellaneous,',
                            u'Features': u'0xff 0xfe 0x2d 0xfe 0xdb 0xff 0x7b 0x87',
                            u'HCI': {u'Revision': u'0x0', 'VERSION': u'4.0 (0x6)'},
                            u'LMP': {u'Subversion': u'0x1b55', 'VERSION': u'4.0 (0x6)'},
                            u'Link mode': u'MASTER',
                            u'Link policy': u'HOLD SNIFF',
                            u'Manufacturer': u'Texas Instruments Inc. (13)',
                            u'Name': u"'FAE39B01'",
                            u'Packet type': u'DM1 DM3 DM5 DH1 DH3 DH5 HV1 HV2 HV3',
                            u'RX': {u'acl': u'0',
                                    u'bytes': u'1267',
                                    u'errors': u'0',
                                    u'events': u'71',
                                    u'sco': u'0'},
                            'SCO_MTU': u'180:4',
                            u'Service Classes': u'Networking',
                            u'TX': {u'acl': u'0',
                                    u'bytes': u'2171',
                                    u'commands': u'71',
                                    u'errors': u'0',
                                    u'sco': u'0'},
                            'TYPE': u'BR/EDR ',
                            'content': [u'hci0:   Type: BR/EDR  Bus: UART',
                                        u'BD Address: 00:17:E9:21:E6:D9  ACL MTU: 1021:4  SCO MTU: 180:4',
                                        u'UP RUNNING PSCAN ISCAN',
                                        u'RX bytes:1267 acl:0 sco:0 events:71 errors:0',
                                        u'TX bytes:2171 acl:0 sco:0 commands:71 errors:0',
                                        u'Features: 0xff 0xfe 0x2d 0xfe 0xdb 0xff 0x7b 0x87',
                                        u'Packet type: DM1 DM3 DM5 DH1 DH3 DH5 HV1 HV2 HV3',
                                        u'Link policy: HOLD SNIFF',
                                        u'Link mode: MASTER',
                                        u"Name: 'FAE39B01'",
                                        u'Class: 0x020000',
                                        u'Service Classes: Networking',
                                        u'Device Class: Miscellaneous,',
                                        u'HCI Version: 4.0 (0x6)  Revision: 0x0',
                                        u'LMP Version: 4.0 (0x6)  Subversion: 0x1b55',
                                        u'Manufacturer: Texas Instruments Inc. (13)']}}
