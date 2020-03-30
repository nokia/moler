# -*- coding: utf-8 -*-
"""
One of Moler's goals is to be IO-agnostic.
So it can be used under twisted, asyncio, curio any any other IO system.

Moler's connection is very thin layer binding Moler's ConnectionObserver with external IO system.
Connection responsibilities:
- have a means for sending outgoing data via external IO
- have a means for receiving incoming data from external IO
- perform data encoding/decoding to let external IO use pure bytes
- have a means allowing multiple observers to get it's received data (data dispatching)
"""

__author__ = 'Grzegorz Latuszek, Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018-2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'

from moler.abstract_moler_connection import AbstractMolerConnection
import logging


def identity_transformation(data):
    """Default coder is no encoding/decoding"""
    logging.log(logging.WARNING, "identity_transformation from connection.py is deprecated now. Please use"
                                 " abstract_moler_connection.py.")
    return data


class Connection(AbstractMolerConnection):
    """Connection API required by ConnectionObservers."""

    def __init__(self, *args, **kwargs):
        super(Connection, self).__init__(*args, **kwargs)
        self._log(logging.WARNING, "Class Connection is deprecated now. Please use AbstractMolerConnection.")
