# -*- coding: utf-8 -*-
"""
enter command module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'


from moler.cmd.unix.genericunix import GenericUnixCommand


class Enter(GenericUnixCommand):

    def __init__(self, connection, prompt=None, newline_chars=None, runner=None):
        super(Enter, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.ret_required = False

    def build_command_string(self):
        return " "


COMMAND_OUTPUT_ver_execute = """
host:~ #
host:~ #"""

COMMAND_KWARGS_ver_execute = {}

COMMAND_RESULT_ver_execute = {}
