# -*- coding: utf-8 -*-
"""
Ip maddr command module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2025, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone


class IpMaddr(GenericUnixCommand):
    def __init__(self, connection, prompt=None, newline_chars=None, options=None, runner=None):
        """
        :param connection: Moler connection to device, terminal when command is executed.
        :param options: unix command options
        :param prompt: prompt (on system where command runs).
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        """
        super(IpMaddr, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.options = options
        self._current_nr = None
        self._current_interface = None
        self.add_failure_indication("is unknown, try \"ip maddr help\".")

    def build_command_string(self) -> str:
        """
        Build command string from parameters passed to object.
        :return: String representation of command to send over connection to device.
        """
        cmd = f"ip maddr"
        if self.options:
            cmd = f"{cmd} {self.options}"
            self.ret_required = True if self.options == 'show' else False
        return cmd

    def on_new_line(self, line: str, is_full_line: bool) -> None:
        """
        Put your parsing code here.
        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: None
        """
        if is_full_line:
            try:
                self._parse_interface(line)
                self._parse_item(line)
            except ParsingDone:
                pass
        return super(IpMaddr, self).on_new_line(line, is_full_line)

    # 1:	lo
    _re_int = re.compile(r"(?P<NR>\d+):\s*(?P<INTERFACE>\S+)")

    def _parse_interface(self, line: str) -> None:
        """
        Parse interface from device.
        :param line: Line from device.
        :return: None but raises ParsingDone if line matches regex.
        """
        if self._regex_helper.match_compiled(IpMaddr._re_int, line):
            self._current_nr = int(self._regex_helper.group('NR'))
            self._current_interface = self._regex_helper.group('INTERFACE')
            self.current_ret[self._current_nr] = {}
            self.current_ret[self._current_nr]['interface'] = self._current_interface
            self.current_ret[self._current_nr]['items'] = []
            raise ParsingDone()

    # inet  224.0.0.251
    _re_item = re.compile(r"\s+(?P<ITEM_TYPE>\S+)\s+(?P<ITEM>\S.*\S)")

    def _parse_item(self, line: str) -> None:
        """
        Parse item from device.
        :param line: Line from device.
        :return: None but raises ParsingDone if line matches regex.
        """
        if self._regex_helper.match_compiled(IpMaddr._re_item, line):
            item_type = self._regex_helper.group('ITEM_TYPE')
            item = self._regex_helper.group('ITEM')
            if self._current_nr is not None:
                self.current_ret[self._current_nr]['items'].append({'type': item_type, 'value': item})
            raise ParsingDone()


COMMAND_OUTPUT = """ip maddr show
1:	lo
    inet  224.0.0.251
    inet  224.0.0.1
    inet6 ff02::fb
    inet6 ff02::1
    inet6 ff01::1
2:	eth0
    link  01:00:5e:00:00:01
    link  33:33:00:00:00:01
    link  33:33:ff:be:a1:3d
    link  01:00:5e:00:00:fb
    link  33:33:00:00:00:fb
    link  33:33:ff:a0:c1:c8
    inet  224.0.0.251
    inet  224.0.0.1
    inet6 ff02::1:ffa0:c1c8
    inet6 ff02::fb
    inet6 ff02::1:ffbe:a13d users 2
    inet6 ff02::1
    inet6 ff01::1
host:~ # """


COMMAND_KWARGS = {
    'options': 'show'
}


COMMAND_RESULT = {
    1: {
        'interface': 'lo',
        'items': [
            {'type': 'inet', 'value': '224.0.0.251'},
            {'type': 'inet', 'value': '224.0.0.1'},
            {'type': 'inet6', 'value': 'ff02::fb'},
            {'type': 'inet6', 'value': 'ff02::1'},
            {'type': 'inet6', 'value': 'ff01::1'},
        ]
    },
    2: {
        'interface': 'eth0',
        'items': [
            {'type': 'link', 'value': '01:00:5e:00:00:01'},
            {'type': 'link', 'value': '33:33:00:00:00:01'},
            {'type': 'link', 'value': '33:33:ff:be:a1:3d'},
            {'type': 'link', 'value': '01:00:5e:00:00:fb'},
            {'type': 'link', 'value': '33:33:00:00:00:fb'},
            {'type': 'link', 'value': '33:33:ff:a0:c1:c8'},
            {'type': 'inet', 'value': '224.0.0.251'},
            {'type': 'inet', 'value': '224.0.0.1'},
            {'type': 'inet6', 'value': 'ff02::1:ffa0:c1c8'},
            {'type': 'inet6', 'value': 'ff02::fb'},
            {'type': 'inet6', 'value': 'ff02::1:ffbe:a13d users 2'},
            {'type': 'inet6', 'value': 'ff02::1'},
            {'type': 'inet6', 'value': 'ff01::1'},
        ]
    }
}
