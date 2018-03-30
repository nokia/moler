# -*- coding: utf-8 -*-
"""
Rm command module.
"""

__author__ = 'Bartosz Odziomek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'bartosz.odziomek@nokia.com'

from moler.cmd.unix.genericunix import GenericUnix
from moler.exceptions import CommandFailure

class Rm(GenericUnix):
    def __init__(self, connection, file, options=None, prompt=None, new_line_chars=None):
        super(Rm, self).__init__(connection)

        self.file = file
        # self.params = parameters
        self.command_string = self.get_cmd()
        self.ret_required = False

        # self._reg_fail = compile(r'(cp\: cannot access)')

    def build_command_string(self):
        if self.options:
            cmd = "{} {} {}".format('rm', self.file, self.options)
        else:
            cmd = "{} {}".format('rm', self.file)
        return cmd

    def on_new_line(self, line, is_full_line):
        if self._cmd_output_started and self._regex_helper.search(r'(rm\: cannot remove)', line):
            self.set_exception(CommandFailure("ERROR: {}".format(self._regex_helper.group(1))))

        return super(Rm, self).on_new_line(line)



COMMAND_OUTPUT = """
user@server:~> cp uses.pl uses.pl.bak
user@server:~>"""

COMMAND_RESULT = {

}

COMMAND_KWARGS = {
    "src": "uses.pl",
    "dst": "uses.pl.bak",
}