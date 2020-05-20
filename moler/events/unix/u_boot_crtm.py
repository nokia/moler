# -*- coding: utf-8 -*-
__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2018-2020, Nokia'
__email__ = 'michal.ernst@nokia.com'

import datetime
import re

from moler.events.unix.genericunix_textualevent import GenericUnixTextualEvent
from moler.exceptions import ParsingDone


class UBootCrtm(GenericUnixTextualEvent):
    def __init__(self, connection, till_occurs_times=-1, runner=None):
        """
        Event for 'Site is resetting due to Fault'
        :param connection: moler connection to device, terminal when command is executed
        :param till_occurs_times: number of event occurrence
        :param runner: Runner to run event
        """
        super(UBootCrtm, self).__init__(connection=connection, runner=runner, till_occurs_times=till_occurs_times)
        self.current_ret = dict()

    def on_new_line(self, line, is_full_line):
        """
         Put your parsing code here.
        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: None
        """
        if is_full_line:
            try:
                self._parse_u_boot_crtm(line)
                self._parse_cpld_version(line)
                self._parse_reset_reason(line)
                self._parse_board_id(line)
                self._parse_gpir(line)
                self._parse_sjmpr(line)
            except ParsingDone:
                pass

    _re_u_boot_crtm = re.compile(r'U-Boot CRTM.*$')

    def _parse_u_boot_crtm(self, line):
        if self._regex_helper.search(UBootCrtm._re_u_boot_crtm, line):
            self.current_ret["time"] = self._last_recv_time_data_read_from_connection

            raise ParsingDone

    _re_cpld_version = re.compile(r'\[CPLD\]\s*Version\s*=(?P<CPLD_version>.*)')

    def _parse_cpld_version(self, line):
        if self._regex_helper.search(UBootCrtm._re_cpld_version, line):
            self.current_ret["CPLD_version"] = self._regex_helper.group("CPLD_version")

            raise ParsingDone

    _re_reset_reason = re.compile(r'Reset\s*Reason\s*[=:](?P<CPLD_reset_reason>.*)')

    def _parse_reset_reason(self, line):
        if self._regex_helper.search(UBootCrtm._re_reset_reason, line):
            self.current_ret["CPLD_reset_reason"] = self._regex_helper.group("CPLD_reset_reason")

            raise ParsingDone

    _re_board_id = re.compile(r'\[CPLD\]\s*Board Id\s*=(?P<CPLD_board_id>.*)')

    def _parse_board_id(self, line):
        if self._regex_helper.search(UBootCrtm._re_board_id, line):
            self.current_ret["CPLD_board_id"] = self._regex_helper.group("CPLD_board_id")

            raise ParsingDone

    _re_gpir = re.compile(r'\[CPLD\]\s*GPIR\s*=(?P<CPLD_gpir>.*)')

    def _parse_gpir(self, line):
        if self._regex_helper.search(UBootCrtm._re_gpir, line):
            self.current_ret["CPLD_gpir"] = self._regex_helper.group("CPLD_gpir")

            raise ParsingDone

    _re_sjmpr = re.compile(r'\[CPLD\]\s*SJMPR\s*=(?P<CPLD_sjmpr>.*)')

    def _parse_sjmpr(self, line):
        if self._regex_helper.search(UBootCrtm._re_sjmpr, line):
            self.current_ret["CPLD_sjmpr"] = self._regex_helper.group("CPLD_sjmpr")
            self.event_occurred(event_data=self.current_ret)
            self.current_ret = dict()

            raise ParsingDone


EVENT_OUTPUT = """

U-Boot CRTM 2013.01-00520-ga4ed750 (Aug 26 2016 - 19:56:14)

SF: Detected MX25U12835E with page size 64 KiB, total 16 MiB

CRTM: Bootflash is not write enabled
CRTM: U-boot state for PARTITION 1 = 0x0fffffff
CRTM: U-boot state for PARTITION 2 = 0x1fffffff
CRTM: Choosing u-boot in PARTITION 2
CRTM: Authenticating u-boot in PARTITION 2

CRTM: Loading u-boot from PARTITION 2



U-Boot 2013.01-00652-g3c5109d (Nov 14 2018 - 11:42:24)

I2C:   ready
DRAM:  2.9 GiB

ARM CLOCK: 1413 MHz [1400 MHz part]
JTAG ID: 2b98102f part b981 variant 2
CPU ID: 412fc0f4 r2p4 rev 0000020a
DIE ID:0x1401300b 0x0c000115
Using default environment


[CPLD] Version      = 0x01.04
[CPLD] Board Id     = 0x20
[CPLD] Reset Reason = [02 00] Reset
[CPLD] GPIR         = 0x17
[CPLD] SJMPR        = 0x00
SF: Detected MX25U12835E with page size 64 KiB, total 16 MiB
"""

EVENT_KWARGS = {
    "till_occurs_times": 1
}

EVENT_RESULT = [
    {
        'time': datetime.datetime(2019, 1, 14, 13, 12, 48, 224929),
        'CPLD_version': ' 0x01.04',
        'CPLD_board_id': ' 0x20',
        'CPLD_reset_reason': ' [02 00] Reset',
        'CPLD_gpir': ' 0x17',
        'CPLD_sjmpr': ' 0x00'
    }
]
