# -*- coding: utf-8 -*-
"""
pwd command module.
"""
import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone

__author__ = 'Yang Snackwell'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'snackwell.yang@nokia-sbell.com'


class Pwd(GenericUnixCommand):

    def __init__(self, connection, prompt=None, newline_chars=None, runner=None):
        super(Pwd, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.ret_required = True

    def build_command_string(self):
        return "pwd"

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_pwd_line(line)
            except ParsingDone:
                pass
        return super(Pwd, self).on_new_line(line, is_full_line)

    _re_pwd_line = re.compile(r"^(?P<full_path>(?P<path_to_current>.*)/(?P<current_path>.*))$")

    def _parse_pwd_line(self, line):
        if self._regex_helper.search_compiled(self._re_pwd_line, line):
            self.current_ret = self._regex_helper.groupdict()
            raise ParsingDone


COMMAND_OUTPUT = """
FZM-TDD-16:/home/emssim/tmp dir/xyz # pwd
/home/emssim/tmp dir/xyz
FZM-TDD-16:/home/emssim/tmp dir/xyz # """

COMMAND_RESULT = {
    'current_path': 'xyz',
    'full_path': '/home/emssim/tmp dir/xyz',
    'path_to_current': '/home/emssim/tmp dir'
}

COMMAND_KWARGS = {}
