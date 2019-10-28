# -*- coding: utf-8 -*-
"""
Generic Unix/Linux module
"""

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'michal.ernst@nokia.com'

import abc
import six
from moler.events.textualevent import TextualEvent
from moler.helpers import remove_xterm_window_title_hack


@six.add_metaclass(abc.ABCMeta)
class GenericUnixTextualEvent(TextualEvent):

    def _decode_line(self, line):
        """
        Decodes line if necessary. Put here code to remove colors from terminal etc.

        :param line: line from device to decode.
        :return: decoded line.
        """
        line = remove_xterm_window_title_hack(line)
        return line
