# -*- coding: utf-8 -*-
"""
Generic Unix/Linux module
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import re

from moler.cmd.commandtextualgeneric import CommandTextualGeneric
from moler.exceptions import CommandFailure
from moler.helpers import remove_escape_codes


class GenericUnixCommand(CommandTextualGeneric):
    _re_fail = re.compile(r'command not found|No such file or directory|running it may require superuser privileges')

    def __init__(self, connection, prompt=None, newline_chars=None, runner=None):
        super(GenericUnixCommand, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                                 runner=runner)
        self.remove_colors_from_terminal_output = True

    def on_new_line(self, line, is_full_line):
        """
        Method to parse command output. Will be called after line with command echo.
        Write your own implementation but don't forget to call on_new_line from base class
        :param line: Line to parse, new lines are trimmed
        :param is_full_line:  False for chunk of line; True on full line (NOTE: new line character removed)
        :return: Nothing
        """
        if is_full_line and self.is_failure_indication(line):
            self.set_exception(CommandFailure(self, "command failed in line '{}'".format(line)))
        return super(GenericUnixCommand, self).on_new_line(line, is_full_line)

    def is_failure_indication(self, line):
        return self._regex_helper.search_compiled(GenericUnixCommand._re_fail, line)

    def _strip_new_lines_chars(self, line):
        line = super(GenericUnixCommand, self)._strip_new_lines_chars(line)
        if self.remove_colors_from_terminal_output:
            line = remove_escape_codes(line)
        return line
