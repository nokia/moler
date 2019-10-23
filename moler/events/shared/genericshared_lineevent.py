# -*- coding: utf-8 -*-
"""
Generic Shared module
"""

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'michal.ernst@nokia.com'

import abc
import six
from moler.events.lineevent import LineEvent


@six.add_metaclass(abc.ABCMeta)
class GenericSharedLineEvent(LineEvent):

    def __new__(cls, *args, **kwargs):
        if cls is GenericSharedLineEvent:
            raise TypeError("Can't instantiate abstract class {}".format(GenericSharedLineEvent.__name__))

        return super(GenericSharedLineEvent, cls).__new__(cls)
