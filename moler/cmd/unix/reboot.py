# -*- coding: utf-8 -*-
"""
Reboot command module.
"""
__author__ = 'Agnieszka Bylica'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'agnieszka.bylica@nokia.com'


from moler.cmd.unix.genericunix import GenericUnixCommand


class Reboot(GenericUnixCommand):

    def __init__(self, connection, prompt=None, newline_chars=None, runner=None):
        """
        :param connection: connection
        :param prompt: Prompt of the starting shell
        :param newline_chars: end of line characters
        """

        super(Reboot, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)

    def build_command_string(self):
        return "reboot"

    def on_new_line(self, line, is_full_line):
        self.set_result({})
        return super(Reboot, self).on_new_line(line, is_full_line)


COMMAND_OUTPUT = """
toor4nsn@fzhub:~# reboot
toor4nsn@fzhub:~#"""

COMMAND_KWARGS = {}

COMMAND_RESULT = {}
