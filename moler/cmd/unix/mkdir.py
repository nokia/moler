# -*- coding: utf-8 -*-
"""
Mkdir command module.
"""
__author__ = 'Sylwester Golonka'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'sylwester.golonka@nokia.com'

from moler.cmd.unix.genericunix import GenericUnix
from moler.exceptions import CommandFailure


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
        if self._cmd_output_started and self._regex_helper.search(
                r'mkdir:\scannot\screate\sdirectory\s(?P<PATH>.*):\s(?P<ERROR>.*)', line):
            self.set_exception(CommandFailure(self, "ERROR: {}".format(self._regex_helper.group("ERROR"))))
        return super(Mkdir, self).on_new_line(line, is_full_line)


COMMAND_OUTPUT = """
user@server:~> mkdir /home/ute/test
user@server:~>"""

COMMAND_RESULT = {

}

COMMAND_KWARGS = {
    "path": "/home/ute/test",
}
