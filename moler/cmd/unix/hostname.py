# -*- coding: utf-8 -*-
"""
Hostname command module.
"""

__author__ = 'Cun Deng'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'cun.deng@nokia-sbell.com'

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone


class Hostname(GenericUnixCommand):

    def __init__(self, connection, options=None, prompt=None, newline_chars=None, runner=None):
        super(Hostname, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                       runner=runner)
        self.options = options

    def build_command_string(self):
        cmd = "hostname"
        if self.options:
            cmd = cmd + " " + self.options
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_user(line)
            except ParsingDone:
                pass
        return super(Hostname, self).on_new_line(line, is_full_line)

    _re_user = re.compile(r"(?P<hostname>\S+)\s*$")

    def _parse_user(self, line):
        if self._regex_helper.search_compiled(Hostname._re_user, line):
            self.current_ret["hostname"] = self._regex_helper.group("hostname")
            raise ParsingDone


COMMAND_OUTPUT = """
ute@cp009-nj:~$ hostname
cp009-nj
ute@cp009-nj:~$ """

COMMAND_RESULT = {
    "hostname": "cp009-nj"
}

COMMAND_KWARGS = {}
