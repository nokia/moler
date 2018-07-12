# -*- coding: utf-8 -*-
"""
Env command module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'


from moler.cmd.unix.genericunix import GenericUnixCommand


class Bash(GenericUnixCommand):

    def __init__(self, connection, prompt=None, new_line_chars=None, bash="TERM=xterm-mono bash"):
        super(Bash, self).__init__(connection, prompt, new_line_chars)
        self.bash = bash
        self.ret_required = False

    def build_command_string(self):
        return self.bash


COMMAND_OUTPUT = """
user@server:~/tmp$ TERM=xterm-mono bash
user@server:~/tmp$"""

COMMAND_RESULT = {}

COMMAND_KWARGS = {}
