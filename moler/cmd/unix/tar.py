# -*- coding: utf-8 -*-
"""
tar command module.
"""
import re

from moler.cmd.unix.genericunix import GenericUnix
from moler.cmd.converterhelper import ConverterHelper
from moler.exceptions import CommandFailure


__author__ = 'Yang Snackwell'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'snackwell.yang@nokia-sbell.com'


class Tar(GenericUnix):
    _re_failed_strings = re.compile("No such file or directory", re.IGNORECASE)

    def __init__(self, connection, prompt=None, new_line_chars=None, options=None, file=None):
        super(Tar, self).__init__(connection, prompt, new_line_chars)
        self._converter_helper = ConverterHelper()
        # Parameters defined by calling the command
        self.options = options
        self.file = file
        self.ret_required = False

    def build_command_string(self):
        if not self.file or not self.options:
            self.set_exception(CommandFailure(self, "Wrong Command Syntax for tar command with options {}, file {}".format(self.options, self.file)))
            return

        cmd = "tar"
        cmd = cmd + " " + self.options + " " + self.file
        return cmd

    def on_new_line(self, line, is_full_line):
        if self.is_failure_indication(line):
            self.set_exception(CommandFailure(self, "command failed in line '{}'".format(line)))
        return super(Tar, self).on_new_line(line, is_full_line)

    def is_failure_indication(self, line):
        return self._regex_helper.search_compiled(Tar._re_failed_strings, line)


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
