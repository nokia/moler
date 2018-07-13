# -*- coding: utf-8 -*-
"""
Mkdir command module.
"""
__author__ = 'Sylwester Golonka'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'sylwester.golonka@nokia.com'

from moler.cmd.unix.genericunix import GenericUnix
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone
import re


class Mkdir(GenericUnix):
    def __init__(self, connection, path, options=None, prompt=None, new_line_chars=None):
        super(Mkdir, self).__init__(connection, prompt=prompt, new_line_chars=new_line_chars)
        self.path = path
        self.options = options
        self.ret_required = False

    def build_command_string(self):
        cmd = "mkdir"
        if self.options:
            cmd = "{} {} {}".format(cmd, self.path, self.options)
        else:
            cmd = "{} {}".format(cmd, self.path)
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_error(line)
            except ParsingDone:
                pass
        return super(Mkdir, self).on_new_line(line, is_full_line)

    _re_parse_error = re.compile(r'mkdir:\scannot\screate\sdirectory\s(?P<PATH>.*):\s(?P<ERROR>.*)')

    def _parse_error(self, line):
        if self._regex_helper.search_compiled(Mkdir._re_parse_error, line):
            self.set_exception(CommandFailure(self, "ERROR: {}".format(self._regex_helper.group("ERROR"))))
            raise ParsingDone


COMMAND_OUTPUT_no_parms = """
user@server:~> mkdir /home/ute/test
user@server:~>"""

COMMAND_RESULT_no_parms = {

}
COMMAND_KWARGS_no_parms = {
    "path": "/home/ute/test",
}

#
COMMAND_OUTPUT_parms = """
user@server:~> mkdir /home/ute/test -m 700
user@server:~>"""

COMMAND_RESULT_parms = {

}
COMMAND_KWARGS_parms = {
    "path": "/home/ute/test",
    "options": "-m 700",
}
