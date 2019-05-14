# -*- coding: utf-8 -*-
"""
SCPI command idn module.
"""

import abc
import six
from moler.cmd.scpi.genricscpi import GenericScpi

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'marcin.usielski@nokia.com'


@six.add_metaclass(abc.ABCMeta)
class GenericScpiNoOutput(GenericScpi):

    def __init__(self, connection, prompt=None, newline_chars=None, runner=None):
        """
        Class for command RST for SCPI device.

        :param connection: connection to device.
        :param prompt: expected prompt sending by device after command execution. Maybe String or compiled re.
        :param newline_chars:  new line chars on device (a list).
        :param runner: runner to run command.
        """
        super(GenericScpiNoOutput, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                                  runner=runner)
        self.ret_required = False
