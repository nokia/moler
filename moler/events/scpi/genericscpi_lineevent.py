# -*- coding: utf-8 -*-
"""
Generic Scpi module
"""

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'michal.ernst@nokia.com'

import abc
import six
from moler.events.lineevent import LineEvent


@six.add_metaclass(abc.ABCMeta)
class GenericScpiLineEvent(LineEvent):

    def __new__(cls, *args, **kwargs):
        if cls is GenericScpiLineEvent:
            raise TypeError("Can't instantiate abstract class {}".format(GenericScpiLineEvent.__name__))

        return super(GenericScpiLineEvent, cls).__new__(cls)
