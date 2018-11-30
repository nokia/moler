# -*- coding: utf-8 -*-
"""
Bash command module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'


from moler.cmd.unix.genericunix import GenericUnixCommand


class Bash(GenericUnixCommand):

    def __init__(self, connection, prompt=None, newline_chars=None, runner=None, bash="TERM=xterm-mono bash"):
        """
        :param connection: Moler connection to device, terminal when command is executed.
        :param prompt: prompt (on system where command runs).
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        :param bash: Command to send over connection to run bash.
        """
        super(Bash, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.bash = bash
        self.ret_required = False

    def build_command_string(self):
        """
        :return: String representation of command to send over connection to device.
        """
        return self.bash


COMMAND_OUTPUT = """
user@server:~/tmp$ TERM=xterm-mono bash
user@server:~/tmp$"""

COMMAND_RESULT = {}

COMMAND_KWARGS = {}
