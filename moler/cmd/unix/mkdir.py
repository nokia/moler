# -*- coding: utf-8 -*-
"""
mkdir command module.
"""

__author__ = 'Sylwester Golonka'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'sylwester.golonka@nokia.com'

from moler.cmd.unix.genericunix import GenericUnix


class Mkdir(GenericUnix):
    def __init__(self, connection, dst, options=None, prompt=None, new_line_chars=None):
        super(Mkdir, self).__init__(connection, prompt, new_line_chars)
        self.dst = dst
        self.options = options

    def build_command_string(self):
        if self.options:
            cmd = "mkdir {} {}".format(self.options, self.dst)
        else:
            cmd = "mkdir {}".format(self.dst)
        return cmd



COMMAND_OUTPUT = ""
COMMAND_KWARGS = {}
COMMAND_RESULT = {}
