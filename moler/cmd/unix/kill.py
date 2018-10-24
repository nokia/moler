# -*- coding: utf-8 -*-
"""
kill command module.
"""

__author__ = 'Yang Yeshu'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'yeshu.yang@nokia-sbell.com'

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone


class Kill(GenericUnixCommand):
    def __init__(self, connection, pid, options=None, prompt=None, newline_chars=None, runner=None):
        super(Kill, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.pid = pid
        self.options = options
        self.ret_required = False

    def build_command_string(self):
        cmd = "kill"
        if self.options:
            cmd = cmd + " " + self.options
        if self.pid:
            cmd = cmd + " " + self.pid
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_no_permit(line)
                self._parse_no_process(line)
            except ParsingDone:
                pass
        return super(Kill, self).on_new_line(line, is_full_line)

    def _parse_no_permit(self, line):
        if self._regex_helper.search(r'(Operation not permitted)', line):
            self.set_exception(CommandFailure(self, "ERROR: {}".format(self._regex_helper.group(1))))
            raise ParsingDone

#    -bash: kill: (973) - No such process
    _re_no_process = re.compile(r"kill: \((?P<Pid>\d+)\) - No such process")

    def _parse_no_process(self, line):
        if self._regex_helper.search_compiled(Kill._re_no_process, line):
            self.current_ret["Pid"] = self._regex_helper.group("Pid")
            raise ParsingDone


COMMAND_OUTPUT_no_process = """
 host:~ # kill -9 973
-bash: kill: (973) - No such process
 host:~ # """

COMMAND_KWARGS_no_process = {
    "pid": "973",
    "options": "-9"
}

COMMAND_RESULT_no_process = {
    "Pid": "973"
}

COMMAND_OUTPUT = """
ttyserver@ttyserver:~> kill 637
ttyserver@ttyserver:~> """

COMMAND_KWARGS = {"pid": "637"}

COMMAND_RESULT = {

}
