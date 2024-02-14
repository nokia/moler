# -*- coding: utf-8 -*-
"""
Command touch module
"""


__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2024, Nokia'
__email__ = 'marcin.usielski@nokia.com'

from moler.cmd.unix.genericunix import GenericUnixCommand


class Touch(GenericUnixCommand):

    def __init__(self, connection, path, prompt=None, newline_chars=None, runner=None, options=None):
        """
        Unix command touch.

        :param connection: Moler connection to device, terminal when command is executed.
        :param path: path to file to be created
        :param prompt: prompt (on system where command runs).
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        :param options: Options of unix touch command
        """
        super(Touch, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.ret_required = False
        self.options = options
        self.path = path
        self.add_failure_indication('touch: cannot touch')

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.

        :return: String representation of command to send over connection to device.
        """
        cmd = "touch"
        if self.options:
            cmd = f"{cmd} {self.options}"
        cmd = f"{cmd} {self.path}"
        return cmd


COMMAND_OUTPUT = """touch file1.txt
moler_bash#"""


COMMAND_KWARGS = {'path': 'file1.txt'}


COMMAND_RESULT = {}


COMMAND_OUTPUT_options = """touch -a file1.txt
moler_bash#"""


COMMAND_KWARGS_options = {'path': 'file1.txt', 'options': '-a'}


COMMAND_RESULT_options = {}
