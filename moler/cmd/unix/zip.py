# -*- coding: utf-8 -*-
"""
Zip command module.
"""

__author__ = 'Haili Guo'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'haili.guo@nokia-sbell.com'


import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure, ParsingDone


class Zip(GenericUnixCommand):

    def __init__(self, connection, options, file_name, zip_file, timeout=60, prompt=None, newline_chars=None,
                 runner=None):
        super(Zip, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        # Parameters defined by calling the command
        self.options = options
        self.file_name = file_name
        self.zip_file = zip_file
        self.ret_required = False
        self.timeout = timeout

    def build_command_string(self):
        if self.options:
            cmd = "{} {} {} {}".format("zip", self.options, self.zip_file, self.file_name)
        else:
            cmd = "{} {} {}".format("zip", self.zip_file, self.file_name)
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_error_via_output_line(line)
            except ParsingDone:
                pass  # line has been fully parsed by one of above parse-methods
        return super(Zip, self).on_new_line(line, is_full_line)

    _re_zip_line = re.compile(r'(?P<error>zip error:.*)')

    def _parse_error_via_output_line(self, line):
        if self._cmd_output_started and self._regex_helper.search_compiled(Zip._re_zip_line, line):
            self.set_exception(CommandFailure(self, "ERROR: {}".format(self._regex_helper.group("error"))))
            raise ParsingDone


COMMAND_OUTPUT = """
host:~ # zip test.zip test.txt
  adding: test.txt (deflated 76%)
host:~ # """

COMMAND_RESULT = {
}

COMMAND_KWARGS = {
    "options": "",
    "zip_file": "test.zip",
    "file_name": "test.txt",
}
