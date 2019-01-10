# -*- coding: utf-8 -*-
"""
Sync command module.
"""

__author__ = 'Julia Patacz, Bartosz Odziomek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'julia.patacz@nokia.com, bartosz.odziomek@nokia.com'

from moler.cmd.unix.genericunix import GenericUnixCommand


class Sync(GenericUnixCommand):
    def __init__(self, connection, prompt=None, newline_chars=None, runner=None):
        """
        :param connection: moler connection to device, terminal when command is executed
        :param prompt: prompt on start system (where command telnet starts).
        :param newline_chars: characters to split lines.
        :param runner: Runner to run command
        """
        super(Sync, self).__init__(connection, prompt, newline_chars, runner=runner)
        self.ret_required = False

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.
        :return: String representation of command to send over connection to device.
        """
        return "sync"


COMMAND_OUTPUT = """
ute@debdev:~/moler$ sync
ute@debdev:~/moler$ """
COMMAND_KWARGS = {}
COMMAND_RESULT = {}
