# -*- coding: utf-8 -*-
"""
Tail command module.
"""
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone
import re

__author__ = 'Sylwester Golonka, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2020, Nokia'
__email__ = 'sylwester.golonka@nokia.com, marcin.usielski@nokia.com'


class Tail(GenericUnixCommand):
    def __init__(self, connection, path, options=None, prompt=None, newline_chars=None, runner=None):
        """
        :param connection: Moler connection to device, terminal when command is executed.
        :param path: path to file to tail.
        :param options: options passed to command tail.
        :param prompt: prompt (on system where command runs).
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        """
        super(Tail, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.path = path
        self.options = options
        self.current_ret["LINES"] = []
        self._line_nr = 0

    def build_command_string(self):
        """
        Builds string with command.

        :return: String with command.
        """
        cmd = "tail"
        if self.options:
            cmd = "{} {} {}".format(cmd, self.path, self.options)
        else:
            cmd = "{} {}".format(cmd, self.path)
        return cmd

    _re_parse_error = re.compile(r'tail:\s(?P<PATH>.*):\s(?P<ERROR>.*)')

    def _parse_error(self, line):
        if self._regex_helper.search_compiled(Tail._re_parse_error, line):
            self.set_exception(CommandFailure(self, "ERROR: {}".format(self._regex_helper.group("ERROR"))))
            raise ParsingDone

    def is_failure_indication(self, line):
        """
        Method to detect if passed line contains part indicating failure of command

        :param line: Line from command output on device
        :return: Match object if find regex in line, None otherwise.
        """
        if self._line_nr > 1:
            if self._stored_exception:
                self._stored_exception = None
            return None
        self._parse_error(line=line)
        return super(Tail, self).is_failure_indication(line=line)

    def _parse_line(self, line):
        if not line == "":
            self.current_ret["LINES"].append(line)
        raise ParsingDone

    def on_new_line(self, line, is_full_line):
        """
        Parses the output of the command.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: None
        """
        if is_full_line:
            self._line_nr += 1
            try:
                self._parse_line(line)
            except ParsingDone:
                pass
        return super(Tail, self).on_new_line(line, is_full_line)


COMMAND_OUTPUT = """
user@host:~$ tail /proc/meminfo
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
user@host:~$
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
                            u'user@host:~$']}

COMMAND_KWARGS = {
    "path": "/proc/meminfo"
}
