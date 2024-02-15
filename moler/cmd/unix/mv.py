# -*- coding: utf-8 -*-
"""
Mv command module.
"""

__author__ = 'Maciej Malczyk'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'maciej.malczyk@nokia.com'
import re
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure, ParsingDone


class Mv(GenericUnixCommand):
    def __init__(self, connection, src, dst, options=None, prompt=None, newline_chars=None, runner=None):
        super(Mv, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)

        self.src = src
        self.dst = dst
        self.options = options
        self.ret_required = False

    def build_command_string(self):
        return f"mv {self.src} {self.dst} {self.options}" if self.options else f"mv {self.src} {self.dst}"

    def on_new_line(self, line, is_full_line):
        if self._cmd_output_started:
            try:
                self._parse_errors(line)
            except ParsingDone:
                pass
        return super(Mv, self).on_new_line(line, is_full_line)

    _reg_fail = re.compile(
        r'(mv: cannot (re)?move .*?: Permission denied'
        r'|mv: cannot stat .*?: No such file or directory'
        r'|mv: cannot create regular file .*?: Permission denied'
        r'|mv: .*? are the same file)')

    def _parse_errors(self, line):
        if self._regex_helper.search(Mv._reg_fail, line):
            self.set_exception(CommandFailure(self, f"ERROR: {self._regex_helper.group(1)}"))
            raise ParsingDone


COMMAND_OUTPUT_NO_FLAGS = """
ute@debdev:~$ mv moving_test.txt moving_tested.txt
ute@debdev:~$"""

COMMAND_RESULT_NO_FLAGS = {

}

COMMAND_KWARGS_NO_FLAGS = {
    "src": "moving_test.txt",
    "dst": "moving_tested.txt",
}

COMMAND_OUTPUT_WITH_FLAGS = """
ute@debdev:~$ mv moving_test moving_tested -f
ute@debdev:~$"""

COMMAND_RESULT_WITH_FLAGS = {}

COMMAND_KWARGS_WITH_FLAGS = {
    "src": "moving_test",
    "dst": "moving_tested",
    "options": "-f"
}
