# -*- coding: utf-8 -*-
"""
Whoami command module.
"""
import re

from moler.cmd.unix.genericunix import GenericUnix
from moler.cmd.converterhelper import ConverterHelper

__author__ = 'Yeshu Yang'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'yeshu.yang@nokia.com'


class Whoami(GenericUnix):

    _re_user = re.compile(r"(\S+)\s*$")

    def __init__(self, connection, prompt=None, new_line_chars=None):
        super(Whoami, self).__init__(connection, prompt, new_line_chars)
        self._converter_helper = ConverterHelper()

    def build_command_string(self):
        cmd = "whoami"
        return cmd

    def on_new_line(self, line, is_full_line):
        if not is_full_line:
            return super(Whoami, self).on_new_line(line, is_full_line)
        if self._regex_helper.search_compiled(Whoami._re_user, line):
            self.current_ret["USER"] = self._regex_helper.group(1)
        return super(Whoami, self).on_new_line(line, is_full_line)


COMMAND_OUTPUT = """
host:~ # whoami
ute
host:~ #"""

COMMAND_RESULT = {
    "USER": "ute"
}

COMMAND_KWARGS = {}
