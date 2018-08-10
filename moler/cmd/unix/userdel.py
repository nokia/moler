# -*- coding: utf-8 -*-
"""
Userdel command module.
"""

__author__ = 'Agnieszka Bylica'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'agnieszka.bylica@nokia.com'


import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone


class Userdel(GenericUnixCommand):
    def __init__(self, connection, prompt=None, new_line_chars=None, options=None, user=None):
        super(Userdel, self).__init__(connection=connection, prompt=prompt, new_line_chars=new_line_chars)

        self.options = options
        self.user = user

        self.current_ret['RESULT'] = list()

    def build_command_string(self):
        cmd = "userdel"
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_line(line)
            except ParsingDone:
                pass
        return super(Userdel, self).on_new_line(line, is_full_line)
