# -*- coding: utf-8 -*-

"""
Moler implementation of MolerConnection for Runner with single thread.
"""


__author__ = "Marcin Usielski"
__copyright__ = "Copyright (C) 2021, Nokia"
__email__ = "marcin.usielski@nokia.com"


import threading
import time

import moler.connection_observer
from moler.abstract_moler_connection import identity_transformation
from moler.observer_thread_wrapper import (
    ObserverThreadWrapper,
    ObserverThreadWrapperForConnectionObserver,
)
from moler.runner_single_thread import RunnerSingleThread
from moler.threaded_moler_connection import ThreadedMolerConnection


class MolerConnectionForSingleThreadRunner(ThreadedMolerConnection):

    """Moler implementation of MolerConnection for Runner with single thread."""

    _runner = None  # One runner for all connections.
    _runner_lock = threading.Lock()

    def __init__(
        self,
        how2send=None,
        encoder=identity_transformation,
        decoder=identity_transformation,
        name=None,
        newline="\n",
        logger_name="",
    ):
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
        super(MolerConnectionForSingleThreadRunner, self).__init__(
            how2send,
            encoder,
            decoder,
            name=name,
            newline=newline,
            logger_name=logger_name,
        )
        self._connection_observers = []
        self.open()

    def open(self):
        """
        Open MolerConnection.

        :return: None
        """
        self.get_runner()
        super(MolerConnectionForSingleThreadRunner, self).open()

    def get_runner(self):
        """
        Get runner to run command and events (instances od ConnectionObsrver).
        :return: Instance of RunnerSingleThread
        """
        with MolerConnectionForSingleThreadRunner._runner_lock:
            if MolerConnectionForSingleThreadRunner._runner is None:
                MolerConnectionForSingleThreadRunner._runner = RunnerSingleThread()
        return MolerConnectionForSingleThreadRunner._runner

    def subscribe_connection_observer(self, connection_observer):
        """
        Subscribe connection observer instance (commands and events).

        :param connection_observer: Command or event.
        :return: None
        """
        if connection_observer not in self._connection_observers:
            self._connection_observers.append(connection_observer)
            self.subscribe(
                observer=connection_observer.data_received,
                connection_closed_handler=connection_observer.connection_closed_handler,
            )

    def unsubscribe_connection_observer(self, connection_observer):
        """
        Unsubscribe connection observer instance (commands and events).

        :param connection_observer: Command or event.
        :return: None
        """
        if connection_observer in self._connection_observers:
            self._connection_observers.remove(connection_observer)
            self.unsubscribe(
                observer=connection_observer.data_received,
                connection_closed_handler=connection_observer.connection_closed_handler,
            )

    def notify_observers(self, data, recv_time):
        """
        Notify all subscribed observers about data received on connection.
        :param data: data to send to all registered subscribers.
        :param recv_time: time of data really read form connection.
        :return None
        """
        super(MolerConnectionForSingleThreadRunner, self).notify_observers(
            data=data, recv_time=recv_time
        )
        for connection_observer in self._connection_observers:
            connection_observer.life_status.last_feed_time = time.monotonic()

    def _create_observer_wrapper(self, observer_reference, self_for_observer):
        """
        Create wrapper for observer to provide separate thread for every callbacks etc.
        :param observer_reference: reference to observer
        :param self_for_observer: reference to object for observer_reference. None if observer_reference is a reference
         to a function.
        :return: Instance of wrapper.
        """
        if self._is_connection_observer_instance(self_for_observer) is True:
            otw = ObserverThreadWrapperForConnectionObserver(
                observer=observer_reference,
                observer_self=self_for_observer,
                logger=self.logger,
            )
        else:
            otw = ObserverThreadWrapper(
                observer=observer_reference,
                observer_self=self_for_observer,
                logger=self.logger,
            )
        return otw

    def _is_connection_observer_instance(self, self_for_observer):
        """
        Check if argument is an instance of subclass of ConnectionObserver.
        :param self_for_observer: object to check.
        :return: True if observer_reference is a subclass of ConnectionObserver, False otherwise.
        """
        if self_for_observer is None:
            return False
        if isinstance(self_for_observer, moler.connection_observer.ConnectionObserver):
            return True
        return False
