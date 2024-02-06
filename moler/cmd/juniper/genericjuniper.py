# -*- coding: utf-8 -*-
"""
Generic juniper module.
"""

import abc
import six
from moler.cmd.commandtextualgeneric import CommandTextualGeneric


__author__ = 'Sylwester Golonka'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'sylwester.golonka@nokia.com'


@six.add_metaclass(abc.ABCMeta)
class GenericJuniperCommand(CommandTextualGeneric):
    """Genericjunipercommand command class."""

    def __init__(self, connection, prompt=None, newline_chars=None, runner=None):
        """
        Genericjunipercommand command.

        :param connection: moler connection to device, terminal when command is executed.
        :param prompt: expected prompt sending by device after command execution
        :param newline_chars: Characters to split lines
        :param runner: Runner to run command
        """
        super(GenericJuniperCommand, self).__init__(connection, prompt=prompt, newline_chars=newline_chars,
                                                    runner=runner)
