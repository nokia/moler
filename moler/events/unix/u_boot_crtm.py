# -*- coding: utf-8 -*-
import datetime

from moler.exceptions import ParsingDone

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com'

import re
from moler.events.textualevent import TextualEvent


class UBootCRTM(TextualEvent):
    def __init__(self, connection, till_occurs_times=-1):
        """
        Event for 'Site is resetting due to Fault'
        :param connection: moler connection to device, terminal when command is executed
        :param fault_id: fault id to catch
        :param till_occurs_times: number of event occurrence
        """
        super(UBootCRTM, self).__init__(connection=connection, till_occurs_times=till_occurs_times)
        self.current_ret = dict()

    def on_new_line(self, line, is_full_line):
        """
         Put your parsing code here.
        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: Nothing
        """
        if is_full_line:
            try:
                self._re_u_boot_crtm(line)
                self._parse_cpld_version(line)
                self._parse_reset_reason(line)
                self._parse_board_id(line)
                self._parse_gpir(line)
                self._parse_sjmpr(line)
            except ParsingDone:
                pass
        return super(UBootCRTM, self).on_new_line(line, is_full_line)

    _re_u_boot_crtm = re.compile(r'U-Boot CRTM.*$')

    def _parse_u_boot_crtm(self, line):
        if self._regex_helper.search(UBootCRTM._re_u_boot_crtm, line):
            self.current_ret["time"] = datetime.datetime.now()

            raise ParsingDone

    _re_cpld_version = re.compile(r'\[CPLD\]\s*Version\s*=(?P<CPLD_version>.*)')

    def _parse_cpld_version(self, line):
        if self._regex_helper.search(UBootCRTM._re_cpld_version, line):
            self.current_ret = dict()
            self.current_ret["CPLD_version"] = self._regex_helper.group("CPLD_version")

            raise ParsingDone

    _re_reset_reason = re.compile(r'Reset\s*Reason\s*[=:](?P<CPLD_reset_reason>.*)')

    def _parse_reset_reason(self, line):
        if self._regex_helper.search(UBootCRTM._re_reset_reason, line):
            self.current_ret = dict()
            self.current_ret["CPLD_reset_reason"] = self._regex_helper.group("CPLD_reset_reason")

            raise ParsingDone

    _re_board_id = re.compile(r'\[CPLD\]\s*Board Id\s*=(?P<CPLD_board_id>.*)')

    def _parse_board_id(self, line):
        if self._regex_helper.search(UBootCRTM._re_board_id, line):
            self.current_ret = dict()
            self.current_ret["CPLD_board_id"] = self._regex_helper.group("CPLD_board_id")

            raise ParsingDone

    _re_gpir = re.compile(r'\[CPLD\]\s*GPIR\s*=(?P<CPLD_gpir>.*)')

    def _parse_gpir(self, line):
        if self._regex_helper.search(UBootCRTM._re_gpir, line):
            self.current_ret = dict()
            self.current_ret["CPLD_gpir"] = self._regex_helper.group("CPLD_gpir")

            raise ParsingDone

    _re_sjmpr = re.compile(r'\[CPLD\]\s*SJMPR\s*=(?P<CPLD_sjmpr>.*)')

    def _parse_sjmpr(self, line):
        if self._regex_helper.search(UBootCRTM._re_sjmpr, line):
            self.current_ret = dict()
            self.current_ret["CPLD_sjmpr"] = self._regex_helper.group("CPLD_sjmpr")
            self.event_occurred(event_data=self.current_ret)

            raise ParsingDone
