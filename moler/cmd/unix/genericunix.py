# -*- coding: utf-8 -*-
"""
Generic Unix/Linux module
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2024, Nokia'
__email__ = 'marcin.usielski@nokia.com'


from moler.cmd.commandtextualgeneric import CommandTextualGeneric
from moler.exceptions import CommandFailure
from moler.helpers import remove_all_known_special_chars
from moler.abstract_moler_connection import AbstractMolerConnection
from moler.runner import ConnectionObserverRunner
from typing import Optional, Pattern, Union, Tuple

import re
import abc
import six


cmd_failure_causes = ['not found',
                      'No such file or directory',
                      'running it may require superuser privileges',
                      'Cannot find device',
                      'Input/output error',
                      ]
r_cmd_failure_cause_alternatives = r'{}'.format("|".join(cmd_failure_causes))


@six.add_metaclass(abc.ABCMeta)
class GenericUnixCommand(CommandTextualGeneric):

    def __init__(self, connection: AbstractMolerConnection, prompt: Optional[Union[str, Pattern]] = None,
                 newline_chars: Optional[Union[list, tuple]] = None, runner: Optional[ConnectionObserverRunner] = None):
        """
        :param connection: Moler connection to device, terminal when command is executed.
        :param prompt: prompt (on system where command runs).
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        """
        super(GenericUnixCommand, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                                 runner=runner)
        self.remove_all_known_special_chars_from_terminal_output = True
        self.re_fail = re.compile(r_cmd_failure_cause_alternatives, re.IGNORECASE)

    def _decode_line(self, line: str) -> str:
        """
        Method to delete new line chars and other chars we don not need to parse in on_new_line (color escape character)

        :param line: Line with special chars, raw string from device
        :return: line without special chars.
        """
        if self.remove_all_known_special_chars_from_terminal_output:
            line = remove_all_known_special_chars(line)
        return line
