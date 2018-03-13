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
import weakref
from threading import Lock
import six
import logging

from moler.exceptions import WrongUsage
from moler.helpers import instance_id
from moler.config.loggers import RAW_DATA, TRACE, TracedIn

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'


def identity_transformation(data):
    """Default coder is no encoding/decoding"""
    return data


class Connection(object):
    """Connection API required by ConnectionObservers."""

    def __init__(self, how2send=None, encoder=identity_transformation, decoder=identity_transformation,
                 logger=None):
        """
        Create Connection via registering external-IO
        :param how2send: any callable performing outgoing IO
        """
        super(Connection, self).__init__()
        self.how2send = how2send or self._unknown_send
        self._encoder = encoder
        self._decoder = decoder
        self.logger = logger

    def __str__(self):
        return '{}(id:{})'.format(self.__class__.__name__, instance_id(self))

    def __repr__(self):
        cmd_str = self.__str__()
        # sender_str = "<Don't know>"
        sender_str = "?"
        if self.how2send != self._unknown_send:
            sender_str = repr(self.how2send)
        # return '{}, how2send {})'.format(cmd_str[:-1], sender_str)
        return '{}-->[{}]'.format(cmd_str, sender_str)

    def send(self, data, timeout=30):  # TODO: should timeout be property of IO? We timeout whole connection-observer.
        """Outgoing-IO API: Send data over external-IO."""
        if self.logger:
            self.logger.info(data, extra={'transfer_direction': '>'})
        data2send = self.encode(data)
        if self.logger:
            self.logger.log(RAW_DATA, data2send, extra={'transfer_direction': '>'})
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
        if self.logger:
            self.logger.error(err_msg)
        raise WrongUsage(err_msg)


class ObservableConnection(Connection):
    """
    Allows objects to subscribe for notification about connection's data-received.
    Subscription is made by registering function to be called with this data (may be object's method).
    Function should have signature like:

    def observer(data):
        # handle that data
    """

    def __init__(self, how2send=None, encoder=identity_transformation, decoder=identity_transformation,
                 logger=None):
        """
        Create Connection via registering external-IO
        :param how2send: any callable performing outgoing IO
        """
        super(ObservableConnection, self).__init__(how2send, encoder, decoder, logger=logger)
        self._observers = dict()
        self._observers_lock = Lock()

    def data_received(self, data):
        """
        Incoming-IO API:
        external-IO should call this method when data is received
        """
        if self.logger:
            self.logger.log(RAW_DATA, data, extra={'transfer_direction': '<'})
        decoded_data = self.decode(data)
        if self.logger:
            self.logger.info(decoded_data, extra={'transfer_direction': '<'})
        self.notify_observers(decoded_data)

    @TracedIn('moler.connection')
    def subscribe(self, observer):
        """
        Subscribe for 'data-received notification'
        :param observer: function to be called
        """
        with self._observers_lock:
            observer_key, value = self._get_observer_key_value(observer)
            if observer_key not in self._observers:
                self._observers[observer_key] = value

    @TracedIn('moler.connection')
    def unsubscribe(self, observer):
        """
        Unsubscribe from 'data-received notification'
        :param observer: function that was previously subscribed
        """
        with self._observers_lock:
            observer_key, _ = self._get_observer_key_value(observer)
            if observer_key in self._observers:
                del self._observers[observer_key]
            else:
                pass  # TODO: put warning into logs

    def notify_observers(self, data):
        """Notify all subscribed observers about data received on connection"""
        # need copy since calling subscribers may change self._observers
        current_subscribers = list(self._observers.values())
        for self_or_none, observer_function in current_subscribers:
            try:
                log_info = r'notifying {}({})'.format(observer_function, data)
                logging.getLogger('moler.connection').log(TRACE, log_info, extra={'transfer_direction': '<'})
                if self_or_none is None:
                    observer_function(data)
                else:
                    observer_self = self_or_none
                    observer_function(observer_self, data)
            except ReferenceError:
                pass  # ignore: weakly-referenced object no longer exists

    @staticmethod
    @TracedIn('moler.connection')
    def _get_observer_key_value(observer):
        """
        Subscribing methods of objects is tricky::

            class TheObserver(object):
                def __init__(self):
                    self.received_data = []

                def on_new_data(self, data):
                    self.received_data.append(data)

            observer1 = TheObserver()
            observer2 = TheObserver()

            subscribe(observer1.on_new_data)
            subscribe(observer2.on_new_data)
            subscribe(observer2.on_new_data)

        Even if it looks like 2 different subscriptions they all
        pass 3 different bound-method objects (different id()).
        So, to differentiate them we need to "unwind" out of them:
        1) self                      - 2 different id()
        2) function object of class  - all 3 have same id()

        Observer key is pair: (self-id, function-id)
        """
        try:
            self_or_none = six.get_method_self(observer)
            self_id = instance_id(self_or_none)
            self_or_none = weakref.proxy(self_or_none)
        except AttributeError:
            self_id = 0  # default for not bound methods
            self_or_none = None

        try:
            function = six.get_method_function(observer)
        except AttributeError:
            function = observer
        function_id = instance_id(function)

        observer_key = (self_id, function_id)
        observer_value = (self_or_none, weakref.proxy(function))
        return observer_key, observer_value
