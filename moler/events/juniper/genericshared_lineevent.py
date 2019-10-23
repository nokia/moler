# -*- coding: utf-8 -*-
"""
Generic Juniper module
"""

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'michal.ernst@nokia.com'

import abc
import six
import datetime

from moler.events.lineevent import LineEvent


@six.add_metaclass(abc.ABCMeta)
class GenericJuniperLineEvent(LineEvent):

    def __new__(cls, *args, **kwargs):
        if cls is GenericJuniperLineEvent:
            raise TypeError("Can't instantiate abstract class {}".format(GenericJuniperLineEvent.__name__))

        return super(GenericJuniperLineEvent, cls).__new__(cls)