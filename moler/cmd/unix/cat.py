# -*- coding: utf-8 -*-
"""
Cat command module.
"""
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone
import re

__author__ = 'Sylwester Golonka'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'sylwester.golonka@nokia.com'


class Cat(GenericUnixCommand):
    def __init__(self, connection, path, options=None, prompt=None, newline_chars=None, runner=None):
        super(Cat, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.path = path
        self.options = options
        self.current_ret["LINES"] = []

    def build_command_string(self):
        cmd = "cat"
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
        return super(Cat, self).on_new_line(line, is_full_line)

    _re_parse_error = re.compile(r'cat:\s(?P<PATH>.*):\s(?P<ERROR>.*)')

    def _parse_error(self, line):
        if self._regex_helper.search_compiled(Cat._re_parse_error, line):
            self.set_exception(CommandFailure(self, "ERROR: {}".format(self._regex_helper.group("ERROR"))))
            raise ParsingDone

    def _parse_line(self, line):
        if not line == "":
            self.current_ret["LINES"].append(line)
        raise ParsingDone


COMMAND_OUTPUT_no_parms = """
ute@debdev:~$ cat /etc/network/interfaces
# This file describes the network interfaces available on your system
# and how to activate them. For more information, see interfaces(5).

source /etc/network/interfaces.d/*
# The loopback network interface

auto lo
iface lo inet loopback
ute@debdev:~$
"""

COMMAND_RESULT_no_parms = {
    'LINES': ['# This file describes the network interfaces available on your system',
              '# and how to activate them. For more information, see interfaces(5).',
              'source /etc/network/interfaces.d/*',
              '# The loopback network interface',
              'auto lo',
              'iface lo inet loopback',
              'ute@debdev:~$']

}
COMMAND_KWARGS_no_parms = {
    "path": "/etc/network/interfaces",
}

#
COMMAND_OUTPUT_parms = """
ute@debdev:~$ cat /etc/network/interfaces -b
     1	# This file describes the network interfaces available on your system
     2	# and how to activate them. For more information, see interfaces(5).
     3	source /etc/network/interfaces.d/*
     4	# The loopback network interface
     5	auto lo
     6	iface lo inet loopback
ute@debdev:~$
"""
COMMAND_RESULT_parms = {
    'LINES': ['     1\t# This file describes the network interfaces available on your system',
              '     2\t# and how to activate them. For more information, see interfaces(5).',
              '     3\tsource /etc/network/interfaces.d/*',
              '     4\t# The loopback network interface',
              '     5\tauto lo',
              '     6\tiface lo inet loopback',
              'ute@debdev:~$']

}
COMMAND_KWARGS_parms = {
    "path": "/etc/network/interfaces",
    "options": "-b",
}
