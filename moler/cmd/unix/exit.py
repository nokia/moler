# -*- coding: utf-8 -*-
"""
Exit command module.
"""

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com'

from moler.cmd.unix.genericunix import GenericUnix
from moler.textualgeneric import TextualGeneric
from moler.exceptions import ParsingDone


class Exit(GenericUnix):
    def __init__(self, connection, prompt=None, expected_prompt=r'^bash-\d+\.*\d*', new_line_chars=None):
        super(Exit, self).__init__(connection=connection, prompt=prompt, new_line_chars=new_line_chars)
        self.ret_required = False
        # Parameters defined by calling the command
        self._re_expected_prompt = TextualGeneric._calculate_prompt(expected_prompt)  # Expected prompt on device

    def build_command_string(self):
        cmd = "exit"
        return cmd

    def on_new_line(self, line, is_full_line):
        try:
            self._is_target_prompt(line)
        except ParsingDone:
            pass  # line has been fully parsed by one of above parse-methods
        return super(Exit, self).on_new_line(line, is_full_line)

    def _is_target_prompt(self, line):
        if self._regex_helper.search_compiled(self._re_expected_prompt, line):
            raise ParsingDone


COMMAND_OUTPUT = """
amu012@belvedere07:~$ exit
bash-4.2:~ #"""

COMMAND_KWARGS = {
}

COMMAND_RESULT = {}
