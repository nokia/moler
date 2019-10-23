# -*- coding: utf-8 -*-
"""
Generic Unix/Linux module
"""

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'michal.ernst@nokia.com'

import abc
import six
from moler.events.lineevent import LineEvent


@six.add_metaclass(abc.ABCMeta)
class GenericUnixLineEvent(LineEvent):

    def __new__(cls, *args, **kwargs):
        if cls is GenericUnixLineEvent:
            raise TypeError("Can't instantiate abstract class {}".format(GenericUnixLineEvent.__name__))

        return super(GenericUnixLineEvent, cls).__new__(cls)
