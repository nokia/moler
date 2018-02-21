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
from threading import Lock

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018 Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'


class WrongUsage(Exception):
    """Wrong usage of library"""
    pass


def identity_transformation(data):
    """Default coder is no encoding/decoding"""
    return data


class Connection(object):
    """Connection API required by ConnectionObservers."""

    def __init__(self, how2send=None, encoder=identity_transformation, decoder=identity_transformation):
        """
        Create Connection via registering external-IO
        :param how2send: any callable performing outgoing IO
        """
        super(Connection, self).__init__()
        self.how2send = how2send or self._unknown_send
        self._encoder = encoder
        self._decoder = decoder

    def send(self, data, timeout=30):  # TODO: should timeout be property of IO? We timeout whole connection-observer.
        """Outgoing-IO API: Send data over external-IO."""
        data2send = self.encode(data)
        self.how2send(data2send)

    def data_received(self, data):
        """Incoming-IO API: external-IO should call this method when data is received"""
        pass

    def encode(self, data):
        """Prepare data for Outgoing-IO"""
        encoded_data = self._encoder(data)
        return encoded_data

    def decode(self, data):
        """Process data from Incoming-IO"""
        decoded_data = self._decoder(data)
        return decoded_data

    def _unknown_send(self, data2send):
        err_msg = "Can't send('{}')".format(data2send)
        err_msg += "\nYou haven't installed sending method of external-IO system"
        err_msg += "\n{}: {}(how2send=external_io_send)".format("Do it either during connection construction",
                                                                self.__class__.__name__)
        err_msg += "\nor later via attribute direct set: connection.how2send = external_io_send"
        raise WrongUsage(err_msg)


class ObservableConnection(Connection):
    """
    Allows objects to subscribe for notification about connection's data-received.
    Subscription is made by registering function to be called with this data (may be object's method).
    Function should have signature like::

    def observer(data):
        # handle that data
    """

    def __init__(self, how2send=None, encoder=identity_transformation, decoder=identity_transformation):
        """
        Create Connection via registering external-IO
        :param how2send: any callable performing outgoing IO
        """
        super(ObservableConnection, self).__init__(how2send, encoder, decoder)
        self._observers = set()
        self._observers_lock = Lock()

    def data_received(self, data):
        """Incoming-IO API: external-IO should call this method when data is received"""
        decoded_data = self.decode(data)
        self.notify_observers(decoded_data)

    def subscribe(self, observer):
        """
        Subscribe for 'data-received notification'
        :param observer: function to be called
        """
        with self._observers_lock:
            self._observers.add(observer)

    def unsubscribe(self, observer):
        """
        Unsubscribe from 'data-received notification'
        :param observer: function that was previously subscribed
        """
        with self._observers_lock:
            self._observers.remove(observer)

    def notify_observers(self, data):
        """Notify all subscribed observers about data received on connection"""
        current_subscribers = set(self._observers)  # need copy since calling subscribers may change self._observers
        for observer in current_subscribers:
            observer(data)
