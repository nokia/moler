# -*- coding: utf-8 -*-
"""
External-IO connections.

The only 3 requirements for these connections is:
(1) store Moler's connection inside self.moler_connection attribute
(2) forward IO received data into self.moler_connection.data_received(data)
(3) provide Moler connection with method to send outgoing data:

  self.moler_connection.how2send = self.send

We want all connections of this subpackage to have
open()/close() API
even that for memory connection that may have no sense
but for majority (tcp, udp, ssh, process ...) it applies,
so lets have common API.
Moreover, we will map it to context manager API.

send()/receive() is required but we cant force naming here since
it's better to keep native/well-known naming of external-IO
(send/recv for socket, transport.write/data_received for asyncio, ...)
Specific external-IO implementation must do data-forwarding and
send-plugin as stated above.
NOTE: send/receive works on bytes since encoding/decoding
is responsibility of moler_connection

So, below class is not needed to work as base class. It may, but
rather it is generic template how to glue external-IO with Moler's connection.
"""

__author__ = 'Grzegorz Latuszek, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com'

import logging
from threading import Lock
import contextlib


class IOConnection(object):
    """External-IO connection."""

    def __init__(self, moler_connection):
        """
        Specific constructor of external-IO should store information
        how to establish connection (like host/port info)

        :param moler_connection: object of abstract class moler.connection.Connection
        """
        super(IOConnection, self).__init__()
        self._connect_subscribers = list()
        self._connect_subscribers_lock = Lock()
        self._disconnect_subscribers = list()
        self._disconnect_subscribers_lock = Lock()
        self.moler_connection = moler_connection
        self.__name = "UNNAMED_IO_CONNECTION"
        self.logger = logging.getLogger("moler.connection.{}.io".format(self.__name))
        # plugin the way we output data to external world
        self.moler_connection.how2send = self.send

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, value):
        self.__name = value
        self.logger = logging.getLogger("moler.connection.{}.io".format(self.__name))

    def open(self):
        """
        Take 'how to establish connection' info from constructor
        and open that connection.

        Return context manager to allow for:  with connection.open() as conn:
        """
        return contextlib.closing(self)

    def close(self):
        """Close established connection."""
        pass

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False  # reraise exceptions if any

    def send(self, data):
        """
        Send data bytes over external-IO.

        Because of plugin done in constructor it will be called
        by moler_connection when it needs.
        """
        pass

    def receive(self):
        """
        Pull data bytes from external-IO:

            data = io_connection.receive()

        and then forward it to Moler's connection:

            self.moler_connection.data_received(data)

        """
        pass

    def data_received(self, data, recv_time):
        """
        Having been given data bytes from external-IO:

        just forward it to Moler's connection:
        """
        self.moler_connection.data_received(data=data, recv_time=recv_time)

    def notify(self, callback, when):
        """
        Adds subscriber to list of functions to call
        :param callback: reference to function to call when connection is open/established
        :param when: connection state change
        :return: None
        """
        if when == "connection_made":
            self.subscribe_on_connection_made(subscriber=callback)
        elif when == "connection_lost":
            self.subscribe_on_connection_lost(subscriber=callback)

    def subscribe_on_connection_made(self, subscriber):
        """
        Adds subscriber to list of functions to call when connection is open/established (also reopen after close)
        :param subscriber: reference to function to call when connection is open/established
        :return: None
        """
        self._subscribe(self._connect_subscribers_lock, self._connect_subscribers, subscriber)

    def subscribe_on_connection_lost(self, subscriber):
        """
        Adds subscriber to list of functions to call when connection is closed/disconnected
        :param subscriber: reference to function to call when connection is closed/disconnected
        :return: None
        """
        self._subscribe(self._disconnect_subscribers_lock, self._disconnect_subscribers, subscriber)

    def unsubscribe_on_connection_made(self, subscriber):
        """
        Remove subscriber from list of functions to call when connection is open/established (also reopen after close)
        :param subscriber: reference to function registered by method subscribe_on_connection_made
        :return: None
        """
        self._unsubscribe(self._connect_subscribers_lock, self._connect_subscribers, subscriber)

    def unsubscribe_on_connection_lost(self, subscriber):
        """
        Remove subscriber from list of functions to call when connection is closed/disconnected
        :param subscriber: reference to function registered by method subscribe_on_connection_lost
        :return: None
        """
        self._unsubscribe(self._disconnect_subscribers_lock, self._disconnect_subscribers, subscriber)

    def _notify(self, lock, subscribers):
        with lock:
            copied_subscribers = subscribers[:]
            for subscriber in copied_subscribers:
                subscriber(self)

    def _notify_on_connect(self):
        self.logger.info(
            msg="Connection to: '{}' has been opened.".format(self.name),
            extra={'log_name': self.name}
        )
        self._notify(self._connect_subscribers_lock, self._connect_subscribers)

    def _notify_on_disconnect(self):
        self.logger.info(
            msg="Connection to: '{}' has been closed.".format(self.name),
            extra={'log_name': self.name}
        )
        self._notify(self._disconnect_subscribers_lock, self._disconnect_subscribers)

    def _subscribe(self, lock, subscribers, subscriber):
        with lock:
            if subscriber not in subscribers:
                subscribers.append(subscriber)

    def _unsubscribe(self, lock, subscribers, subscriber):
        with lock:
            subscribers.remove(subscriber)
