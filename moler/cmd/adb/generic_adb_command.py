"""
Generic for adb commands.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2022, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import abc
import six

from moler.cmd.commandtextualgeneric import CommandTextualGeneric


@six.add_metaclass(abc.ABCMeta)
class GenericAdbCommand(CommandTextualGeneric):
    pass
