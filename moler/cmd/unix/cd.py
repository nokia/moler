# -*- coding: utf-8 -*-
"""
cd command module.
"""

__author__ = 'Michal Ernst, Marcin Usielski, Tomasz Krol'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'michal.ernst@nokia.com, marcin.usielski@nokia.com, tomasz.krol@nokia.com'


from moler.exceptions import ParsingDone
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.cmd.commandtextualgeneric import CommandTextualGeneric


class Cd(GenericUnixCommand):

    def __init__(self, connection, path=None, prompt=None, newline_chars=None, runner=None, expected_prompt=None):
        """
        :param connection: moler connection to device
        :param prompt: start prompt (on system where command cd starts)
        :param path: path to directory
        :param expected_prompt: Prompt after change directory
        :param newline_chars: Characters to split lines
        :param runner: Runner to run command
        """
        super(Cd, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)

        # Parameters defined by calling the command
        self.path = path

        # command parameters
        self.ret_required = False
        self._re_expected_prompt = None
        if expected_prompt:
            self._re_expected_prompt = CommandTextualGeneric._calculate_prompt(expected_prompt)  # Expected prompt on device

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.
        :return: String representation of command to send over connection to device.
        """
        cmd = "cd"
        if self.path:
            cmd = f"{cmd} {self.path}"
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Put your parsing code here.
        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: None
        """
        if self._re_expected_prompt is not None:
            try:
                self._is_target_prompt(line)
            except ParsingDone:
                pass  # line has been fully parsed by one of above parse-methods
        else:
            super(Cd, self).on_new_line(line, is_full_line)

    def _is_target_prompt(self, line):
        """
        Checks target prompt.
        :param line: Line to process
        :return: None
        """
        if self._regex_helper.search_compiled(self._re_expected_prompt, line):
            if not self.done():
                self.set_result({})
                raise ParsingDone

# -----------------------------------------------------------------------------
# Following documentation is required for library CI.
# It is used to perform command self-test.
# Parameters:
# path is Optional.Path for Unix cd command
# -----------------------------------------------------------------------------


COMMAND_OUTPUT_ver_execute = """
host:~ # cd /home/ute/
host:/home/ute #
"""

COMMAND_KWARGS_ver_execute = {'path': '/home/ute'}

COMMAND_RESULT_ver_execute = {
}

COMMAND_OUTPUT_ver_expected_prompt = """
host:~ # cd /home/ute/test
host:/home/ute/test #
"""

COMMAND_KWARGS_ver_expected_prompt = {'path': '/home/ute/test', 'expected_prompt': r'host:/home/ute/test #'}

COMMAND_RESULT_ver_expected_prompt = {
}
