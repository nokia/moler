# -*- coding: utf-8 -*-
"""
PDU generic module for commands in state PDU.
"""

import six
import abc
from moler.cmd.commandtextualgeneric import CommandTextualGeneric

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'marcin.usielski@nokia.com'


@six.add_metaclass(abc.ABCMeta)
class GenericPduAten(CommandTextualGeneric):
    def __init__(self, connection, prompt=None, newline_chars=None, runner=None):
        """
        Base class for Aten PDU commands in all states.

        :param connection: connection to device.
        :param prompt: expected prompt sending by device after command execution. Maybe String or compiled re.
        :param runner: runner to run command.
        """

        super(GenericPduAten, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                             runner=runner)
