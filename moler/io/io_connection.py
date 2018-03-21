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

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'


class IOConnection(object):
    """External-IO connection."""

    def __init__(self, moler_connection):
        """
        Specific constructor of external-IO should store information
        how to establish connection (like host/port info)
        """
        super(IOConnection, self).__init__()
        self.moler_connection = moler_connection
        # plugin the way we output data to external world
        self.moler_connection.how2send = self.send

    def open(self):
        """
        Take 'how to establish connection' info from constructor
        and open that connection.
        """
        pass

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

    def data_received(self, data):
        """
        Having been given data bytes from external-IO:

        just forward it to Moler's connection:
        """
        self.moler_connection.data_received(data)
