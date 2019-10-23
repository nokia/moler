# -*- coding: utf-8 -*-
"""
Generic Juniper_Ex module
"""

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'michal.ernst@nokia.com'

import abc
import six
from moler.events.lineevent import LineEvent


@six.add_metaclass(abc.ABCMeta)
class GenericJuniperExLineEvent(LineEvent):

    def __new__(cls, *args, **kwargs):
        if cls is GenericJuniperExLineEvent:
            raise TypeError("Can't instantiate abstract class {}".format(GenericJuniperExLineEvent.__name__))

        return super(GenericJuniperExLineEvent, cls).__new__(cls)
