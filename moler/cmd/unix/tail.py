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
    def __init__(self, connection, path, options=None, prompt=None, newline_chars=None, runner=None):
        super(Tail, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
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
ute@debdev:~$ tail /proc/meminfo
VmallocChunk:   34359608824 kB
HardwareCorrupted:     0 kB
AnonHugePages:         0 kB
HugePages_Total:       0
HugePages_Free:        0
HugePages_Rsvd:        0
HugePages_Surp:        0
Hugepagesize:       2048 kB
DirectMap4k:       53184 kB
DirectMap2M:     4141056 kB
ute@debdev:~$
"""

COMMAND_RESULT = {'LINES': [u'VmallocChunk:   34359608824 kB',
                            u'HardwareCorrupted:     0 kB',
                            u'AnonHugePages:         0 kB',
                            u'HugePages_Total:       0',
                            u'HugePages_Free:        0',
                            u'HugePages_Rsvd:        0',
                            u'HugePages_Surp:        0',
                            u'Hugepagesize:       2048 kB',
                            u'DirectMap4k:       53184 kB',
                            u'DirectMap2M:     4141056 kB',
                            u'ute@debdev:~$']}

COMMAND_KWARGS = {
    "path": "/proc/meminfo"
}
