# -*- coding: utf-8 -*-
"""
Echo command module.
"""
__author__ = 'Agnieszka Bylica'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'agnieszka.bylica@nokia.com'


import re
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone


class Echo(GenericUnixCommand):
    def __init__(self, connection, prompt=None, new_line_chars=None):
        super(Echo, self).__init__(connection=connection, prompt=prompt, new_line_chars=new_line_chars)

    def build_command_string(self):
        cmd = "echo"
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                pass
            except ParsingDone:
                pass
        return super(Echo, self).on_new_line(line, is_full_line)
