# -*- coding: utf-8 -*-
"""
Generic juniperex module.
"""

import abc
import six
from moler.cmd.commandtextualgeneric import CommandTextualGeneric

__author__ = 'Sylwester Golonka'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'sylwester.golonka@nokia.com'


@six.add_metaclass(abc.ABCMeta)
class GenericJuniperEXCommand(CommandTextualGeneric):
    """Genericjuniperexcommand command class."""
