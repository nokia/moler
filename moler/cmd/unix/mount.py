# -*- coding: utf-8 -*-
"""
Mount command module.
"""

__author__ = 'Agnieszka Bylica'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'agnieszka.bylica@nokia.com'


import re

from moler.cmd.commandtextualgeneric import CommandTextualGeneric
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone


class Mount(GenericUnixCommand):

    def __init__(self, connection, options=None, prompt=None, new_line_chars=None):
        super(Mount, self).__init__(connection=connection, prompt=prompt, new_line_chars=new_line_chars)

        # Parameters defined by calling the command
        self.options = options

        # Internal variables
        self.current_ret['RESULT'] = list()

    def build_command_string(self):
        cmd = "mount"
        if self.options:
            cmd = cmd + " " + self.options
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._command_failure(line)
                self._parse(line)
            except ParsingDone:
                pass
        elif self._is_prompt(line):
            if not self.done():
                self.set_result({})
        return super(Mount, self).on_new_line(line, is_full_line)
