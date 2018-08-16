# -*- coding: utf-8 -*-
"""
SFTP command module.
"""
__author__ = 'Agnieszka Bylica'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'agnieszka.bylica@nokia.com'


from moler.cmd.unix.genericunix import GenericUnixCommand
# from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone


class Sftp(GenericUnixCommand):
    def __init__(self, connection, prompt=None, new_line_chars=None):
        super(Sftp, self).__init__(connection=connection, prompt=prompt, new_line_chars=new_line_chars)

    def build_command_string(self):
        cmd = "sftp"
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                pass
            except ParsingDone:
                pass

        super(Sftp, self).on_new_line(line, is_full_line)
