# -*- coding: utf-8 -*-
"""
Cat command module.
"""
import logging

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone
from moler.exceptions import CommandTimeout
import re

__author__ = 'Sylwester Golonka, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2023, Nokia'
__email__ = 'sylwester.golonka@nokia.com, marcin.usielski@nokia.com'


class Cat(GenericUnixCommand):
    def __init__(self, connection, path, options=None, prompt=None, newline_chars=None, runner=None,
                 failure_only_in_first_line=True):
        """
        :param connection: Moler connection to device, terminal when command is executed.
        :param path: path to file to cat.
        :param options: options passed to command cat.
        :param prompt: prompt (on system where command runs).
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        :param failure_only_in_first_line: Set False to find errors in all lines, True otherwise.
        """
        super(Cat, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.path = path
        self.options = options
        self.failure_only_in_first_line = failure_only_in_first_line
        self.current_ret["LINES"] = []
        self._line_nr = 0
        self._exception_warn = False

    def build_command_string(self):
        """
        Builds string with command.

        :return: String with command.
        """
        cmd = "cat"
        if self.options:
            cmd = f"{cmd} {self.path} {self.options}"
        else:
            cmd = f"{cmd} {self.path}"
        return cmd

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
        return super(Cat, self).on_new_line(line, is_full_line)

    # cat: moler.log: Permission denied
    _re_parse_error = re.compile(r'^.*:.*:\s*(No such file or directory|command not found|Permission denied|'
                                 r'Is a directory)$')

    def set_exception(self, exception):
        """
        Set exception object as failure for command object.

        :param exception: An exception object to set.
        :return: None
        """
        if self.failure_only_in_first_line and self._line_nr > 1 and not isinstance(exception, CommandTimeout):
            if self._exception_warn is False:
                self._log(logging.WARNING, f"The exception ({exception}) is tried to be set but was ignored (requested).")
            self._exception_warn = True
            return
        return super(Cat, self).set_exception(exception)

    def is_failure_indication(self, line, is_full_line):
        """
        Method to detect if passed line contains part indicating failure of command.

        :param line: Line from command output on device
        :return: Match object if find regex in line, None otherwise.
        """
        return self._regex_helper.search_compiled(Cat._re_parse_error, line) is not None

    def _parse_line(self, line):
        if not line == "":
            self.current_ret["LINES"].append(line)
        raise ParsingDone


COMMAND_OUTPUT_no_parms = """cat /etc/network/interfaces
# This file describes the network interfaces available on your system
# and how to activate them. For more information, see interfaces(5).

source /etc/network/interfaces.d/*
# The loopback network interface

auto lo
iface lo inet loopback
user@host:~$
"""

COMMAND_RESULT_no_parms = {
    'LINES': ['# This file describes the network interfaces available on your system',
              '# and how to activate them. For more information, see interfaces(5).',
              'source /etc/network/interfaces.d/*',
              '# The loopback network interface',
              'auto lo',
              'iface lo inet loopback',
              'user@host:~$']

}
COMMAND_KWARGS_no_parms = {
    "path": "/etc/network/interfaces",
}

COMMAND_OUTPUT_cannot_open = """cat file.txt
Some output
No such file or directory
user@host:~$"""

COMMAND_RESULT_cannot_open = {
    'LINES':
        [
            'Some output',
            'No such file or directory',
        ],
}

COMMAND_KWARGS_cannot_open = {
    "path": "file.txt",
}

COMMAND_OUTPUT_no_such_file_or_directory = """cat file.txt

2020-06-23T12:02:42.328562+02:00 info 5GBTS-143-OAM-000 ext-sshd[980136]: lastlog_openseek: Couldn't stat /var/log/lastlog: No such file or directory
other lines
user@host:~$"""

COMMAND_RESULT_no_such_file_or_directory = {
    'LINES':
        [
            r"2020-06-23T12:02:42.328562+02:00 info 5GBTS-143-OAM-000 ext-sshd[980136]: lastlog_openseek: Couldn't stat /var/log/lastlog: No such file or directory",
            r"other lines"
        ],
}

COMMAND_KWARGS_no_such_file_or_directory = {
    "path": "file.txt",
}


COMMAND_OUTPUT_parms = """cat /etc/network/interfaces -b
     1	# This file describes the network interfaces available on your system
     2	# and how to activate them. For more information, see interfaces(5).
     3	source /etc/network/interfaces.d/*
     4	# The loopback network interface
     5	auto lo
     6	iface lo inet loopback
user@host:~$
"""

COMMAND_RESULT_parms = {
    'LINES': ['     1\t# This file describes the network interfaces available on your system',
              '     2\t# and how to activate them. For more information, see interfaces(5).',
              '     3\tsource /etc/network/interfaces.d/*',
              '     4\t# The loopback network interface',
              '     5\tauto lo',
              '     6\tiface lo inet loopback',
              'user@host:~$']

}

COMMAND_KWARGS_parms = {
    "path": "/etc/network/interfaces",
    "options": "-b",
}
