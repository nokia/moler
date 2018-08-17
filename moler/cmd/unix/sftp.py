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
    def __init__(self, connection, host, user="", password=None, pathname=None, new_pathname=None, batch_file=None, prompt=None, new_line_chars=None):
        super(Sftp, self).__init__(connection=connection, prompt=prompt, new_line_chars=new_line_chars)

        self.host = host
        self.user = user
        self.password = password
        # For command without interactive session pathname or batch_file should be obligatory
        self.pathname = pathname
        self.new_pathname = new_pathname
        self.batch_file = batch_file

    def build_command_string(self):
        cmd = "sftp"
        if self.batch_file:
            cmd = "{} -b {}".format(cmd, self.batch_file)
        if self.user:
            cmd = "{} {}@{}".format(cmd, self.user, self.host)
        else:
            cmd = "{} {}".format(cmd, self.host)
        if self.pathname:
            cmd = "{}:{}".format(cmd, self.pathname)
        if self.new_pathname:
            cmd = "{} {}".format(cmd, self.new_pathname)
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                pass
            except ParsingDone:
                pass

        super(Sftp, self).on_new_line(line, is_full_line)


COMMAND_OUTPUT = ""
COMMAND_KWARGS = {}
COMMAND_RESULT = {}
