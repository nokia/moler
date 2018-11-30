# -*- coding: utf-8 -*-
"""
Run script command
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure


class RunScript(GenericUnixCommand):

    def __init__(self, connection, script_command, error_regex=re.compile("error", re.I), prompt=None, newline_chars=None, runner=None):
        """
        :param connection: Moler connection to device, terminal when command is executed.
        :param script_command: path to script to run.
        :param error_regex: Regex to detect error in script output.l
        :param prompt: prompt (on system where command runs).
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        """
        super(RunScript, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                        runner=runner)
        self.script_command = script_command
        self.error_regex = error_regex
        self.ret_required = False

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.
        :return: String representation of command to send over connection to device.
        """
        return self.script_command

    def on_new_line(self, line, is_full_line):
        """
        Put your parsing code here.
        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: Nothing
        """
        if self.error_regex and self._regex_helper.search_compiled(self.error_regex, line):
            self.set_exception(CommandFailure(self, "Found error regex in line '{}'".format(line)))
        return super(RunScript, self).on_new_line(line, is_full_line)


COMMAND_OUTPUT = """
ute@debdev:~$ ./myscript.sh
Output from script
ute@debdev:~$"""

COMMAND_KWARGS = {"script_command": "./myscript.sh"}

COMMAND_RESULT = {}
