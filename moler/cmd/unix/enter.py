# -*- coding: utf-8 -*-
"""
enter command module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'marcin.usielski@nokia.com'


from moler.cmd.unix.genericunix import GenericUnixCommand


class Enter(GenericUnixCommand):

    def __init__(self, connection, prompt=None, newline_chars=None, runner=None):
        """
        :param connection: Moler connection to device, terminal when command is executed.
        :param prompt: prompt (on system where command runs).
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        """
        super(Enter, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.ret_required = False

    def build_command_string(self):
        """
        :return: String representation of command to send over connection to device.
        """
        return ""


COMMAND_OUTPUT_ver_execute = """
host:~ #
host:~ #"""

COMMAND_KWARGS_ver_execute = {}

COMMAND_RESULT_ver_execute = {}
