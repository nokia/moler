# -*- coding: utf-8 -*-
"""
Hexdump command module.
"""

__author__ = 'Agnieszka Bylica, Adrianna Pienkowska'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'agnieszka.bylica@nokia.com, adrianna.pienkowska@nokia,com'

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

    def build_command_string(self):
        cmd = "hexdump"
        if self.options:
            cmd = cmd + " " + self.options
        if self.files and self._is_file():
            for file in self.files:
                cmd = cmd + ' {}'.format(file)
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse(line)
            except ParsingDone:
                pass
        return super(Hexdump, self).on_new_line(line, is_full_line)

    def _parse(self, line):
        self.current_ret["RESULT"].append(line)
        raise ParsingDone

    def _is_file(self):
        is_empty = True
        for file in self.files:
            if file and file.strip(" \t\n\r\f\v"):
                is_empty = False
        if is_empty:
            self.set_excetion(CommandFailure(self, "No files given to hexdump: {}".format(self.files)))
        return True
