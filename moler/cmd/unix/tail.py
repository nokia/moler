# -*- coding: utf-8 -*-
"""
Tail command module.
"""
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone
import re

__author__ = 'Sylwester Golonka'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'sylwester.golonka@nokia.com'


class Tail(GenericUnixCommand):
    def __init__(self, connection, path, options=None, prompt=None, new_line_chars=None):
        super(Tail, self).__init__(connection, prompt=prompt, new_line_chars=new_line_chars)
        self.path = path
        self.options = options
        self.current_ret["LINES"] = []

    def build_command_string(self):
        cmd = "tail"
        if self.options:
            cmd = "{} {} {}".format(cmd, self.path, self.options)
        else:
            cmd = "{} {}".format(cmd, self.path)
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_error(line)
                self._parse_line(line)
            except ParsingDone:
                pass
        return super(Tail, self).on_new_line(line, is_full_line)

    _re_parse_error = re.compile(r'tail:\s(?P<PATH>.*):\s(?P<ERROR>.*)')

    def _parse_error(self, line):
        if self._regex_helper.search_compiled(Tail._re_parse_error, line):
            self.set_exception(CommandFailure(self, "ERROR: {}".format(self._regex_helper.group("ERROR"))))
            raise ParsingDone

    def _parse_line(self, line):
        if not line == "":
            self.current_ret["LINES"].append(line)
        raise ParsingDone


COMMAND_OUTPUT = """
root@fzm-lsp-k2:~# tail /rom/btsom/reset_reason_log.txt
tail -n 10 /rom/btsom/reset_reason_log.txt
Site Manager DeltaPush:2013.01.05_16.12.22:BMGR
NetAct initiated configuration change:2013.01.05_16.45.56:BMGR
Site Manager DeltaPush:2013.01.05_19.58.24:BMGR
NetAct initiated configuration change:2013.01.05_20.07.31:BMGR
NetAct initiated configuration change:2013.01.05_20.42.25:BMGR
root@fzm-lsp-k2:~#
"""

COMMAND_RESULT = {'LINES': [u'tail -n 10 /rom/btsom/reset_reason_log.txt',
                            u'Site Manager DeltaPush:2013.01.05_16.12.22:BMGR',
                            u'NetAct initiated configuration change:2013.01.05_16.45.56:BMGR',
                            u'Site Manager DeltaPush:2013.01.05_19.58.24:BMGR',
                            u'NetAct initiated configuration change:2013.01.05_20.07.31:BMGR',
                            u'NetAct initiated configuration change:2013.01.05_20.42.25:BMGR',
                            u'root@fzm-lsp-k2:~#']}

COMMAND_KWARGS = {
    "path": "/rom/btsom/reset_reason_log.txt"
}
