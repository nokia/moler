# -*- coding: utf-8 -*-
"""
Dmesg command module.
"""
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone

__author__ = 'Sylwester Golonka'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'sylwester.golonka@nokia.com'


class Dmesg(GenericUnixCommand):
    def __init__(self, connection, options=None, prompt=None, newline_chars=None, runner=None):
        super(Dmesg, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.options = options
        self.current_ret["LINES"] = []

    def build_command_string(self):
        cmd = "dmesg"
        if self.options:
            cmd = "{} {}".format(cmd, self.options)
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_line(line)
            except ParsingDone:
                pass
        return super(Dmesg, self).on_new_line(line, is_full_line)

    def _parse_line(self, line):
        if not line == "":
            self.current_ret["LINES"].append(line)
        raise ParsingDone


COMMAND_OUTPUT = """
root@fzm-lsp-k2:~# dmesg
[616239.693658] ucd9000 1-007e: [UCD9000] UCD interval: 300056 [ms], Linux interval: 300000 [ms], Diff: 56 [ms]
[616239.693674] ucd9000 1-007e: [UCD9000] Clock accuracy OK
[616539.693644] ucd9000 1-007e: [UCD9000] UCD interval: 300018 [ms], Linux interval: 300000 [ms], Diff: 18 [ms]
[616539.693655] ucd9000 1-007e: [UCD9000] Clock accuracy OK
[616839.693513] ucd9000 1-007e: [UCD9000] UCD interval: 299983 [ms], Linux interval: 300000 [ms], Diff: -17 [ms]
[616839.693525] ucd9000 1-007e: [UCD9000] Clock accuracy OK

[755439.693750] ucd9000 1-007e: [UCD9000] UCD interval: 299936 [ms], Linux interval: 300000 [ms], Diff: -64 [ms]
[755439.693761] ucd9000 1-007e: [UCD9000] Clock accuracy OK
[755739.693709] ucd9000 1-007e: [UCD9000] UCD interval: 299920 [ms], Linux interval: 300000 [ms], Diff: -80 [ms]
[755739.693721] ucd9000 1-007e: [UCD9000] Clock accuracy OK
[756039.693730] ucd9000 1-007e: [UCD9000] UCD interval: 299950 [ms], Linux interval: 300000 [ms], Diff: -50 [ms]
[756039.693741] ucd9000 1-007e: [UCD9000] Clock accuracy OK

[778239.693823] ucd9000 1-007e: [UCD9000] Clock accuracy OK
[778539.693523] ucd9000 1-007e: [UCD9000] UCD interval: 299862 [ms], Linux interval: 300000 [ms], Diff: -138 [ms]
[778539.693534] ucd9000 1-007e: [UCD9000] Clock accuracy OK
[778839.693671] ucd9000 1-007e: [UCD9000] UCD interval: 299816 [ms], Linux interval: 300000 [ms], Diff: -184 [ms]
[778839.694219] ucd9000 1-007e: [UCD9000] Clock accuracy exceeds threshold, setting trim to -9.57 [%] (0xd59c)
root@fzm-lsp-k2:~#
"""

COMMAND_RESULT = {'LINES': [
    u'[616239.693658] ucd9000 1-007e: [UCD9000] UCD interval: 300056 [ms], Linux interval: 300000 [ms], Diff: 56 [ms]',
    u'[616239.693674] ucd9000 1-007e: [UCD9000] Clock accuracy OK',
    u'[616539.693644] ucd9000 1-007e: [UCD9000] UCD interval: 300018 [ms], Linux interval: 300000 [ms], Diff: 18 [ms]',
    u'[616539.693655] ucd9000 1-007e: [UCD9000] Clock accuracy OK',
    u'[616839.693513] ucd9000 1-007e: [UCD9000] UCD interval: 299983 [ms], Linux interval: 300000 [ms], Diff: -17 [ms]',
    u'[616839.693525] ucd9000 1-007e: [UCD9000] Clock accuracy OK',
    u'[755439.693750] ucd9000 1-007e: [UCD9000] UCD interval: 299936 [ms], Linux interval: 300000 [ms], Diff: -64 [ms]',
    u'[755439.693761] ucd9000 1-007e: [UCD9000] Clock accuracy OK',
    u'[755739.693709] ucd9000 1-007e: [UCD9000] UCD interval: 299920 [ms], Linux interval: 300000 [ms], Diff: -80 [ms]',
    u'[755739.693721] ucd9000 1-007e: [UCD9000] Clock accuracy OK',
    u'[756039.693730] ucd9000 1-007e: [UCD9000] UCD interval: 299950 [ms], Linux interval: 300000 [ms], Diff: -50 [ms]',
    u'[756039.693741] ucd9000 1-007e: [UCD9000] Clock accuracy OK',
    u'[778239.693823] ucd9000 1-007e: [UCD9000] Clock accuracy OK',
    u'[778539.693523] ucd9000 1-007e: [UCD9000] UCD interval: 299862 [ms], Linux interval: 300000 [ms], Diff: -138 [ms]',
    u'[778539.693534] ucd9000 1-007e: [UCD9000] Clock accuracy OK',
    u'[778839.693671] ucd9000 1-007e: [UCD9000] UCD interval: 299816 [ms], Linux interval: 300000 [ms], Diff: -184 [ms]',
    u'[778839.694219] ucd9000 1-007e: [UCD9000] Clock accuracy exceeds threshold, setting trim to -9.57 [%] (0xd59c)',
    u'root@fzm-lsp-k2:~#']}

COMMAND_KWARGS = {
}
