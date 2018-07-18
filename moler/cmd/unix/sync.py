# -*- coding: utf-8 -*-
"""
Sync command module.
"""

__author__ = 'Julia Patacz'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'julia.patacz@nokia.com'

from moler.cmd.unix.genericunix import GenericUnixCommand


class Sync(GenericUnixCommand):
    def __init__(self, connection, prompt=None, new_line_chars=None):
        super(Sync, self).__init__(connection, prompt, new_line_chars)
        self.ret_required = False

    def build_command_string(self):
        return "sync"


COMMAND_OUTPUT = """
ute@debdev:~/moler$ sync
ute@debdev:~/moler$ """
COMMAND_KWARGS = {}
COMMAND_RESULT = {}
