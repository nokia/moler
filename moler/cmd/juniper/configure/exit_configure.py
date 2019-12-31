# -*- coding: utf-8 -*-
"""
Exitconfigure command module.
"""

__author__ = 'Sylwester Golonka'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'sylwester.golonka@nokia.com'

from moler.cmd.juniper.genericjuniper import GenericJuniperCommand
from moler.exceptions import ParsingDone


class ExitConfigure(GenericJuniperCommand):
    """Configure command class."""

    def __init__(self, connection, prompt=None, expected_prompt=r'^admin@switch>',
                 newline_chars=None, runner=None, target_newline="\r\n"):
        """
        Exitconfigure command.

        :param connection: Moler connection to device, terminal when command is executed.
        :param prompt: Prompt of the starting shell
        :param expected_prompt: Prompt of the target shell reached after exit command
        :param newline_chars: Characters to split lines - list.
        :param target_newline: newline chars on remote system where ssh connects
        :param runner: Runner to run command
        """
        super(ExitConfigure, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                            runner=runner)
        self.ret_required = False
        self.target_newline = target_newline
        # Parameters defined by calling the command
        self._re_expected_prompt = GenericJuniperCommand._calculate_prompt(expected_prompt)  # Expected prompt on device

    def build_command_string(self):
        """
        Build command string from parameters passed to object.

        :return: String representation of command to send over connection to device.
        """
        cmd = "exit"
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Put your parsing code here.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: Nothing
        """
        try:
            self._is_target_prompt(line)
        except ParsingDone:
            pass  # line has been fully parsed by one of above parse-methods

    def _is_target_prompt(self, line):
        """
        Checks target prompt.

        :param line: Line to process
        :return: Nothing
        """
        if self._regex_helper.search_compiled(self._re_expected_prompt, line):
            self.set_result({})
            raise ParsingDone


COMMAND_OUTPUT = """
admin@switch# exit
exit
Exiting configuration mode
admin@switch> """

COMMAND_KWARGS = {
    "expected_prompt": r'admin@switch>'
}

COMMAND_RESULT = {}
