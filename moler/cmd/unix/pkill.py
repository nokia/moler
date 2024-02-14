# -*- coding: utf-8 -*-
"""
Pkill command module.
"""

__author__ = 'Yeshu Yang'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'yeshu.yang@nokia-sbell.com'


from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone


class Pkill(GenericUnixCommand):

    def __init__(self, connection, name, prompt=None, newline_chars=None, runner=None):
        super(Pkill, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.name = name
        self.ret_required = False

    def build_command_string(self):
        cmd = f"pkill {self.name}"
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_no_permit(line)
            except ParsingDone:
                pass
        return super(Pkill, self).on_new_line(line, is_full_line)

    def _parse_no_permit(self, line):
        if self._regex_helper.search(r'(Operation not permitted)', line):
            self.set_exception(CommandFailure(self, f"ERROR: {self._regex_helper.group(1)}"))
            raise ParsingDone


COMMAND_OUTPUT_no_verbose = """
ute@cp19-nj:~$ pkill ping
ute@cp19-nj:~$ """

COMMAND_KWARGS_no_verbose = {"name": "ping"}

COMMAND_RESULT_no_verbose = {

}
