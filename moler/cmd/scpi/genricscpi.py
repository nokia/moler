# -*- coding: utf-8 -*-
"""
SCPI generic module for commands in all states.
"""

import six
import abc
from moler.cmd.commandtextualgeneric import CommandTextualGeneric

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'marcin.usielski@nokia.com'


@six.add_metaclass(abc.ABCMeta)
class GenericScpi(CommandTextualGeneric):

    def __init__(self, connection, prompt=None, newline_chars=None, runner=None):
        """
        Base class for Scpi commands.

        :param connection: connection to device.
        :param prompt: expected prompt sending by device after command execution. Maybe String or compiled re.
        :param newline_chars:  new line chars on device (a list).
        :param runner: runner to run command.
        """

        super(GenericScpi, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                          runner=runner)
        self.current_ret['RAW_OUTPUT'] = list()

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            self.current_ret['RAW_OUTPUT'].append(line)
        return super(GenericScpi, self).on_new_line(line=line, is_full_line=is_full_line)
