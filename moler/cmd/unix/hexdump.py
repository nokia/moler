# -*- coding: utf-8 -*-
"""
Hexdump command module.
"""

__author__ = 'Agnieszka Bylica', 'Adrianna Pienkowska'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'agnieszka.bylica@nokia.com', 'adrianna.pienkowska@nokia.com'

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone
import re


class Hexdump(GenericUnixCommand):
    def __init__(self, connection, files, options=None, prompt=None, new_line_chars=None):
        super(Hexdump, self).__init__(connection=connection, prompt=prompt, new_line_chars=new_line_chars)
        self.options = options
        self.files = files
        self.current_ret['RESULT'] = list()
        self._is_file()

    def build_command_string(self):
        cmd = "hexdump"
        if self.options:
            cmd = cmd + " " + self.options
        if self.files:
            for file in self.files:
                cmd = cmd + ' {}'.format(file)
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._command_failure(line)
                self._parse(line)
            except ParsingDone:
                pass
        return super(Hexdump, self).on_new_line(line, is_full_line)

    def _parse(self, line):
        self.current_ret["RESULT"].append(line)
        raise ParsingDone

    _re_error = re.compile(r"hexdump:\s(?P<ERROR_MSG>.*)", re.IGNORECASE)

    def _command_failure(self, line):
        if self._regex_helper.search_compiled(Hexdump._re_error, line):
            self.set_exception(CommandFailure(self, "ERROR: {}".format(self._regex_helper.group("ERROR_MSG"))))
            raise ParsingDone

    def _is_file(self):
        is_empty = True
        if isinstance(self.files, list):
            for file in self.files:
                if file and file.strip(" \t\n\r\f\v"):
                    is_empty = False
        if is_empty:
            self.set_exception(CommandFailure(self, "No files given to hexdump: {}".format(self.files)))


COMMAND_OUTPUT_proper_use = """
xyz@debian:~$ hexdump old
0000000 6741 0a61 6e41 6169 410a 646e 7a72 6a65
0000010 410a 746e 6e6f 0a69
0000018
xyz@debian:~$"""

COMMAND_KWARGS_proper_use = {
    'files': ["old"]
}

COMMAND_RESULT_proper_use = {
    'RESULT': ['0000000 6741 0a61 6e41 6169 410a 646e 7a72 6a65', '0000010 410a 746e 6e6f 0a69', '0000018']
}


COMMAND_OUTPUT_empty_file = """
xyz@debian:~$ hexdump new
xyz@debian:~$"""

COMMAND_KWARGS_empty_file = {
    'files': ["new"]
}

COMMAND_RESULT_empty_file = {
    'RESULT': []
}


COMMAND_OUTPUT_options = """
xyz@debian:~$ hexdump -b old
0000000 101 147 141 012 101 156 151 141 012 101 156 144 162 172 145 152
0000010 012 101 156 164 157 156 151 012
0000018
xyz@debian:~$"""

COMMAND_KWARGS_options = {
    'files': ["old"],
    'options': '-b'
}

COMMAND_RESULT_options = {
    'RESULT': ['0000000 101 147 141 012 101 156 151 141 012 101 156 144 162 172 145 152',
               '0000010 012 101 156 164 157 156 151 012', '0000018']
}
