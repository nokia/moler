# -*- coding: utf-8 -*-
"""
Generic Unix/Linux module
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2020, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import re
import abc
import six

from moler.cmd.commandtextualgeneric import CommandTextualGeneric
from moler.exceptions import CommandFailure
from moler.helpers import remove_all_known_special_chars

cmd_failure_causes = ['not found',
                      'No such file or directory',
                      'running it may require superuser privileges',
                      'Cannot find device',
                      'Input/output error']
r_cmd_failure_cause_alternatives = r'{}'.format("|".join(cmd_failure_causes))


@six.add_metaclass(abc.ABCMeta)
class GenericUnixCommand(CommandTextualGeneric):
    _re_fail = re.compile(r_cmd_failure_cause_alternatives, re.IGNORECASE)

    def __init__(self, connection, prompt=None, newline_chars=None, runner=None):
        """
        :param connection: Moler connection to device, terminal when command is executed.
        :param prompt: prompt (on system where command runs).
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        """
        super(GenericUnixCommand, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                                 runner=runner)
        self.remove_all_known_special_chars_from_terminal_output = True

    def on_new_line(self, line, is_full_line):
        """
        Method to parse command output. Will be called after line with command echo.
        Write your own implementation but don't forget to call on_new_line from base class

        :param line: Line to parse, new lines are trimmed
        :param is_full_line:  False for chunk of line; True on full line (NOTE: new line character removed)
        :return: None
        """
        if is_full_line and self.is_failure_indication(line):
            self.set_exception(CommandFailure(self, "command failed in line '{}'".format(line)))
        return super(GenericUnixCommand, self).on_new_line(line, is_full_line)

    def is_failure_indication(self, line):
        """
        Method to detect if passed line contains part indicating failure of command

        :param line: Line from command output on device
        :return: Match object if find regex in line, None otherwise.
        """
        if self._re_fail:
            return self._regex_helper.search_compiled(GenericUnixCommand._re_fail, line)
        return None

    def _decode_line(self, line):
        """
        Method to delete new line chars and other chars we don not need to parse in on_new_line (color escape character)

        :param line: Line with special chars, raw string from device
        :return: line without special chars.
        """
        if self.remove_all_known_special_chars_from_terminal_output:
            line = remove_all_known_special_chars(line)
        return line
