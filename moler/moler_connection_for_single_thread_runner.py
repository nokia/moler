# -*- coding: utf-8 -*-

"""
Moler implementation of MolerConnection for Runner with single thread.
"""


__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2021, Nokia'
__email__ = 'marcin.usielski@nokia.com'


from moler.abstract_moler_connection import identity_transformation
from moler.observer_thread_wrapper import ObserverThreadWrapper, ObserverThreadWrapperForConnectionObserver
from moler.connection_observer import ConnectionObserver
from moler.threaded_moler_connection import ThreadedMolerConnection
from moler.runner_with_threaded_moler_connection import RunnerForSingleThread
import time


class MolerConnectionForSingleThreadRunner(ThreadedMolerConnection):
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
        super(MolerConnectionForSingleThreadRunner, self).__init__(how2send, encoder, decoder, name=name,
                                                                   newline=newline,
                                                                   logger_name=logger_name)
        self._runner = None
        self._connection_observers = list()
        self.open()

    def shutdown(self):
        if self._runner:
            self._runner.shutdown()
        self._runner = None
        super(MolerConnectionForSingleThreadRunner, self).shutdown()

    def open(self):
        if self._runner:  # Already open
            return
        self._runner = RunnerForSingleThread(connection=self)
        super(MolerConnectionForSingleThreadRunner, self).open()

    def get_runner(self):
        return self._runner

    def subscribe_connection_observer(self, connection_observer):
        if connection_observer not in self._connection_observers:
            self._connection_observers.append(connection_observer)
            self.subscribe(
                observer=connection_observer.data_received,
                connection_closed_handler=connection_observer.connection_closed_handler
            )

    def unsubscribe_connection_observer(self, connection_observer):
        if connection_observer in self._connection_observers:
            self._connection_observers.remove(connection_observer)
            self.unsubscribe(
                observer=connection_observer.data_received,
                connection_closed_handler=connection_observer.connection_closed_handler
            )

    def notify_observers(self, data, recv_time):
        """
        Notify all subscribed observers about data received on connection.
        :param data: data to send to all registered subscribers.
        :param recv_time: time of data really read form connection.
        :return None
        """
        super(MolerConnectionForSingleThreadRunner, self).notify_observers(data=data, recv_time=recv_time)
        for connection_observer in self._connection_observers:
            connection_observer.life_status.last_feed_time = time.time()

    def _create_observer_wrapper(self, observer_reference, self_for_observer):
        if observer_reference is None or not isinstance(self_for_observer, ConnectionObserver):
            otw = ObserverThreadWrapper(
                observer=observer_reference, observer_self=self_for_observer, logger=self.logger)
        else:
            otw = ObserverThreadWrapperForConnectionObserver(
                observer=observer_reference, observer_self=self_for_observer, logger=self.logger)
        return otw
