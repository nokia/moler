# -*- coding: utf-8 -*-
"""
Md5sum command module.
"""
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone
import re

__author__ = 'Sylwester Golonka'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'sylwester.golonka@nokia.com'


class Md5sum(GenericUnixCommand):
    def __init__(self, connection, path, options=None, prompt=None, newline_chars=None, runner=None):
        super(Md5sum, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.path = path
        self.options = options

    def build_command_string(self):
        cmd = "md5sum"
        if self.options:
            cmd = f"{cmd} {self.path} {self.options}"
        else:
            cmd = f"{cmd} {self.path}"
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_line(line)
            except ParsingDone:
                pass
        return super(Md5sum, self).on_new_line(line, is_full_line)

    _re_parse_line = re.compile(r'(?P<SUM>[\da-f]{32})\s+(?P<FILE>\S+)')

    def _parse_line(self, line):
        if self._regex_helper.search_compiled(Md5sum._re_parse_line, line):
            self.current_ret['SUM'] = self._regex_helper.group("SUM")
            self.current_ret['FILE'] = self._regex_helper.group("FILE")
        raise ParsingDone


COMMAND_OUTPUT_parms = """
ute@debdev:~$ md5sum test.txt
91503d6cac7a663901b30fc400e93644  test.txt
ute@debdev:~$
"""
COMMAND_RESULT_parms = {
    'FILE': 'test.txt',
    'SUM': '91503d6cac7a663901b30fc400e93644'
}
COMMAND_KWARGS_parms = {
    "path": "test.txt",
}
