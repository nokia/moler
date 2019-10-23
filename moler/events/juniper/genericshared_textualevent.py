# -*- coding: utf-8 -*-
"""
Generic Juniper module
"""

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'michal.ernst@nokia.com'

import abc
import six

from moler.events.textualevent import TextualEvent


@six.add_metaclass(abc.ABCMeta)
class GenericJuniperEvent(TextualEvent):
    pass
