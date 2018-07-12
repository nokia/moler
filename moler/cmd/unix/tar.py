# -*- coding: utf-8 -*-
"""
tar command module.
"""

from moler.cmd.unix.genericunix import GenericUnixCommand

__author__ = 'Yang Snackwell'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'snackwell.yang@nokia-sbell.com'


class Tar(GenericUnixCommand):

    def __init__(self, connection, options, file, prompt=None, new_line_chars=None):
        super(Tar, self).__init__(connection, prompt, new_line_chars)
        # Parameters defined by calling the command
        self.options = options
        self.file = file
        self.ret_required = False

    def build_command_string(self):
        cmd = "tar"
        cmd = cmd + " " + self.options + " " + self.file
        return cmd


COMMAND_OUTPUT = """
host:~ # tar xzvf test.tar.gz
test.1
test.2
test.3
host:~ # """

COMMAND_RESULT = {
}

COMMAND_KWARGS = {
    "options": "xzvf",
    "file": "test.tar.gz",
}
