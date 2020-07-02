# -*- coding: utf-8 -*-
"""
PDU generic module for commands in state PDU.
"""

import six
import abc
import re
from moler.cmd.pdu_aten.generic_pdu_aten import GenericPduAten
from moler.exceptions import CommandFailure

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'marcin.usielski@nokia.com'

cmd_failure_causes = ['Not Support',
                      'Invalid command']

r_cmd_failure_cause_alternatives = r'{}'.format("|".join(cmd_failure_causes))


@six.add_metaclass(abc.ABCMeta)
class GenericPdu(GenericPduAten):
    def __init__(self, connection, prompt=None, newline_chars=None, runner=None):
        """
        Base class for Aten PDU commands in state PDU.

        :param connection: connection to device.
        :param prompt: expected prompt sending by device after command execution. Maybe String or compiled re.
        :param newline_chars:  new line chars on device (a list).
        :param runner: runner to run command.
        """
        super(GenericPdu, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                         runner=runner)
        self._re_fail = re.compile(r_cmd_failure_cause_alternatives, re.IGNORECASE)

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
        return super(GenericPdu, self).on_new_line(line, is_full_line)

    def is_failure_indication(self, line):
        """
        Method to detect if passed line contains part indicating failure of command

        :param line: Line from command output on device
        :return: Match object if find regex in line, None otherwise.
        """
        ret = self._regex_helper.search_compiled(self._re_fail, line) if self._re_fail else None
        return ret
