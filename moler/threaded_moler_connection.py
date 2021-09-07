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
__copyright__ = 'Copyright (C) 2018-2021, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'

import weakref
import logging
import six
from threading import Lock
from moler.abstract_moler_connection import AbstractMolerConnection
from moler.abstract_moler_connection import identity_transformation
from moler.config.loggers import RAW_DATA, TRACE
from moler.helpers import instance_id
from moler.observer_thread_wrapper import ObserverThreadWrapper


class ThreadedMolerConnection(AbstractMolerConnection):
    """
    Allows objects to subscribe for notification about connection's data-received.
    Subscription is made by registering function to be called with this data (may be object's method).
    Function should have signature like:

    def observer(data):
        # handle that data
    """

    def __init__(self, how2send=None, encoder=identity_transformation, decoder=identity_transformation,
                 name=None, newline='\n', logger_name=""):
        """
        Create Connection via registering external-IO

        :param how2send: any callable performing outgoing IO
        :param encoder: callable converting data to bytes
        :param decoder: callable restoring data from bytes
        :param name: name assigned to connection
        :param logger_name: take that logger from logging

        Logger is retrieved by logging.getLogger(logger_name)
        If logger_name == "" - take logger "moler.connection.<name>"
        If logger_name is None - don't use logging
        """
        super(ThreadedMolerConnection, self).__init__(how2send, encoder, decoder, name=name, newline=newline,
                                                      logger_name=logger_name)
        self._connection_closed_handlers = dict()
        self._observer_wrappers = dict()
        self._observers_lock = Lock()

    def data_received(self, data, recv_time):
        """
        Incoming-IO API:
        external-IO should call this method when data is received
        """
        if not self.is_open():
            return

        extra = {'transfer_direction': '<', 'encoder': lambda data: data.encode(encoding='utf-8', errors="replace")}
        self._log_data(msg=data, level=RAW_DATA,
                       extra=extra)

        decoded_data = self.decode(data)
        self._log_data(msg=decoded_data, level=logging.INFO,
                       extra=extra)

        self.notify_observers(decoded_data, recv_time)

    def subscribe(self, observer, connection_closed_handler):
        """
        Subscribe for 'data-received notification'

        :param observer: function to be called to notify when data received.
        :param connection_closed_handler: callable to be called when connection is closed.
        """
        self.logger.debug(">>> Entering {}. conn-obs '{}' moler-conn '{}'".format(self._observers_lock, observer, self))
        with self._observers_lock:
            self.logger.debug(">>> Entered  {}. conn-obs '{}' moler-conn '{}'".format(self._observers_lock, observer, self))
            self._log(level=TRACE, msg="subscribe({})".format(observer))
            observer_key, value = self._get_observer_key_value(observer)

            if observer_key not in self._observer_wrappers:
                self_for_observer, observer_reference = value
                self._observer_wrappers[observer_key] = self._create_observer_wrapper(
                    observer_reference=observer_reference, self_for_observer=self_for_observer)
                self._connection_closed_handlers[observer_key] = connection_closed_handler
        self.logger.debug(">>> Exited   {}. conn-obs '{}' moler-conn '{}'".format(self._observers_lock, observer, self))

    def _create_observer_wrapper(self, observer_reference, self_for_observer):
        otw = ObserverThreadWrapper(
            observer=observer_reference, observer_self=self_for_observer, logger=self.logger)
        return otw

    def unsubscribe(self, observer, connection_closed_handler):
        """
        Unsubscribe from 'data-received notification'
        :param observer: function that was previously subscribed
        :param connection_closed_handler: callable to be called when connection is closed.
        """
        self.logger.debug(">>> Entering {}. conn-obs '{}' moler-conn '{}'".format(self._observers_lock, observer, self))
        with self._observers_lock:
            self.logger.debug(">>> Entered  {}. conn-obs '{}' moler-conn '{}'".format(self._observers_lock, observer, self))
            self._log(level=TRACE, msg="unsubscribe({})".format(observer))
            observer_key, _ = self._get_observer_key_value(observer)
            if observer_key in self._observer_wrappers and observer_key in self._connection_closed_handlers:
                self._observer_wrappers[observer_key].request_stop()
                del self._connection_closed_handlers[observer_key]
                del self._observer_wrappers[observer_key]
            else:
                self._log(level=logging.WARNING,
                          msg="{} and {} were not both subscribed.".format(observer, connection_closed_handler),
                          levels_to_go_up=2)
        self.logger.debug(">>> Exited   {}. conn-obs '{}' moler-conn '{}'".format(self._observers_lock, observer, self))

    def shutdown(self):
        """
        Closes connection with notifying all observers about closing.
        :return: None
        """
        for handler in list(self._connection_closed_handlers.values()):
            handler()
        super(ThreadedMolerConnection, self).shutdown()

    def notify_observers(self, data, recv_time):
        """
        Notify all subscribed observers about data received on connection.
        :param data: data to send to all registered subscribers.
        :param recv_time: time of data really read form connection.
        :return None
        """
        subscribers_wrappers = list(self._observer_wrappers.values())
        for wrapper in subscribers_wrappers:
            try:
                self.logger.debug(">>> Queue for notifying. conn-obs '{}' moler-conn '{}' data {}".format(wrapper._observer, self, repr(data)))
            except ReferenceError:
                pass  # wrapper._observer is no more valid
            else:
                wrapper.feed(data=data, recv_time=recv_time)

    @staticmethod
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
            func = six.get_method_function(observer)
        except AttributeError:
            func = observer
        function_id = instance_id(func)

        observer_key = (self_id, function_id)
        observer_value = (self_or_none, weakref.proxy(func))
        return observer_key, observer_value
