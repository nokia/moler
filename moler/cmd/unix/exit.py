# -*- coding: utf-8 -*-
"""
Exit command module.
"""

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com'

from moler.exceptions import ParsingDone
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.cmd.commandtextualgeneric import CommandTextualGeneric


class Exit(GenericUnixCommand):
    def __init__(self, connection, prompt=None, expected_prompt='>', newline_chars=None, runner=None, target_newline="\n"):
        """
        :param connection:
        :param prompt: Prompt of the starting shell
        :param expected_prompt: Prompt of the target shell reached after exit command
        :param newline_chars:
        """
        super(Exit, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.ret_required = False
        self.target_newline = target_newline

        # Parameters defined by calling the command
        self._re_expected_prompt = CommandTextualGeneric._calculate_prompt(expected_prompt)  # Expected prompt on device

    def build_command_string(self):
        cmd = "exit"
        return cmd

    def on_new_line(self, line, is_full_line):
        try:
            self._is_target_prompt(line)
        except ParsingDone:
            pass  # line has been fully parsed by one of above parse-methods

    def _is_target_prompt(self, line):
        if self._regex_helper.search_compiled(self._re_expected_prompt, line):
            if not self.done():
                self.set_result({})
                raise ParsingDone


COMMAND_OUTPUT = """
amu012@belvedere07:~$ exit
bash-4.2:~ #"""

COMMAND_KWARGS = {
    "expected_prompt": r'bash-4.2'
}

COMMAND_RESULT = {}
