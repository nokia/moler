# -*- coding: utf-8 -*-
"""
tar command module.
"""

from moler.cmd.unix.genericunix import GenericUnixCommand

__author__ = 'Yang Snackwell'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'snackwell.yang@nokia-sbell.com'


class Tar(GenericUnixCommand):

    def __init__(self, connection, options, file, prompt=None, newline_chars=None, runner=None):
        super(Tar, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        # Parameters defined by calling the command
        self.options = options
        self.file = file
        self.ret_required = False

    def build_command_string(self):
        cmd = "tar"
        cmd = f"{cmd} {self.options} {self.file}"
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
