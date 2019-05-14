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
    pass
