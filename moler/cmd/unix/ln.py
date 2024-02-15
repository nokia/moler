# -*- coding: utf-8 -*-
"""
Ln command module.
"""

__author__ = 'Haili Guo'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'haili.guo@nokia-sbell.com'

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure, ParsingDone


class Ln(GenericUnixCommand):

    def __init__(self, connection, prompt=None, newline_chars=None, options=None, runner=None):
        super(Ln, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        # Parameters defined by calling the command
        self.options = options
        self.ret_required = False

    def build_command_string(self):
        cmd = "ln"
        if self.options:
            cmd = f"{cmd} {self.options}"
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_failure_via_output_line(line)
            except ParsingDone:
                pass
        return super(Ln, self).on_new_line(line, is_full_line)

    _re_ln_line = re.compile(r'(?P<error>ln:.*File exists)')

    def _parse_failure_via_output_line(self, line):
        if self._cmd_output_started and self._regex_helper.search_compiled(Ln._re_ln_line, line):
            self.set_exception(CommandFailure(self, f"ERROR: {self._regex_helper.group('error')}"))
            raise ParsingDone


COMMAND_OUTPUT = """
user@server:~> ln -s file1 file2
user@server:~>"""


COMMAND_RESULT = {

}


COMMAND_KWARGS = {"options": "-s file1 file2"}
