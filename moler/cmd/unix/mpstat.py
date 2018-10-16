# -*- coding: utf-8 -*-
"""
Mpstat command module.
"""

__author__ = 'Julia Patacz'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'julia.patacz@nokia.com'

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone


class Mpstat(GenericUnixCommand):

    def __init__(self, connection, options=None, prompt=None, newline_chars=None, runner=None):
        super(Mpstat, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        # Parameters defined by calling the command
        self.options = options
        self.ret_required = False
        self.current_ret['cpu'] = []

    def build_command_string(self):
        cmd = "mpstat"
        if self.options:
            cmd = cmd + " " + self.options
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_line(line)
            except ParsingDone:
                pass  # line has been fully parsed by one of above parse-methods
        return super(Mpstat, self).on_new_line(line, is_full_line)

    # 08:27:55     CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest   %idle
    _re_headers = re.compile(
        r"(?P<TIME>\S+)\s+(?P<CPU>\S+)\s+(?P<USR>\d+.\d+)\s+(?P<NICE>\d+.\d+)\s+(?P<SYS>\d+.\d+)\s+(?P<IOWAIT>\d+.\d+)\s+(?P<IRQ>\d+.\d+)\s+(?P<SOFT>\d+.\d+)\s+(?P<STEAL>\d+.\d+)\s+(?P<GUEST>\d+.\d+)\s+(?P<IDLE>\d+.\d+)$")

    _re_keys_table = ['USR', 'NICE', 'SYS', 'IOWAIT', 'IRQ', 'SOFT', 'STEAL', 'GUEST', 'IDLE']

    def _parse_line(self, line):
        if self._regex_helper.search_compiled(Mpstat._re_headers, line):
            if self._regex_helper.group('CPU') != 'CPU':
                temp = {}
                temp[self._regex_helper.group('CPU')] = {}
                temp[self._regex_helper.group('CPU')]['TIME'] = self._regex_helper.group('TIME')
                for key in Mpstat._re_keys_table:
                    try:
                        temp[self._regex_helper.group('CPU')][key] = float(self._regex_helper.group(key))
                    except ValueError:
                        raise CommandFailure("Wrong value type of {}: {}.".format(key, self._regex_helper.group(key)))
                self.current_ret["cpu"].append(temp)
            raise ParsingDone


COMMAND_OUTPUT = """
toor4nsn@fzm-lsp-k2:~# mpstat
Linux 4.4.112-rt127 (fzm-lsp-k2)    05/10/18    _armv7l_    (4 CPU)
11:07:06     CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest   %idle
11:07:06     all    1.50    0.07    2.28    0.50    0.00    0.17    0.00    0.00   95.49
toor4nsn@fzm-lsp-k2:~# """
COMMAND_KWARGS = {
}
COMMAND_RESULT = {
    "cpu": [
        {
            "all": {
                'TIME': '11:07:06',
                'USR': 1.50,
                'NICE': 0.07,
                'SYS': 2.28,
                'IOWAIT': 0.50,
                'IRQ': 0.00,
                'SOFT': 0.17,
                'STEAL': 0.00,
                'GUEST': 0.00,
                'IDLE': 95.49,
            }
        }
    ]
}
