from moler.threaded_moler_connection import ThreadedMolerConnection
from moler.runner import ThreadPoolExecutorRunner


__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2021, Nokia'
__email__ = 'marcin.usielski@nokia.com'


import weakref
import logging
import six
import time
from threading import Lock
from moler.abstract_moler_connection import AbstractMolerConnection
from moler.abstract_moler_connection import identity_transformation
from moler.config.loggers import RAW_DATA, TRACE
from moler.helpers import instance_id
from moler.observer_thread_wrapper import ObserverThreadWrapper


class ThreadedMolerConnectionWithRunner(ThreadedMolerConnection, ThreadPoolExecutorRunner):
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
        self._observers_runner = list()
        self._to_remove_connection_observers = list()

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
        #self._check_observers_loop()

    def subscribe(self, observer, connection_closed_handler):
        """
        Subscribe for 'data-received notification'

        :param observer: function to be called to notify when data received.
        :param connection_closed_handler: callable to be called when connection is closed.
        """
        with self._observers_lock:
            self._log(level=TRACE, msg="subscribe({})".format(observer))
            observer_key, value = self._get_observer_key_value(observer)

            if observer_key not in self._observer_wrappers:
                self_for_observer, observer_reference = value
                self._observer_wrappers[observer_key] = ObserverThreadWrapper(
                    observer=observer_reference, observer_self=self_for_observer, logger=self.logger)
                self._connection_closed_handlers[observer_key] = connection_closed_handler

    def unsubscribe(self, observer, connection_closed_handler):
        """
        Unsubscribe from 'data-received notification'
        :param observer: function that was previously subscribed
        :param connection_closed_handler: callable to be called when connection is closed.
        """
        with self._observers_lock:
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
            wrapper.feed(data=data, recv_time=recv_time)

    def _check_observers_loop(self):
        for connection_observer in self._observers_runner:
            self._feed_loop(connection_observer=connection_observer, stop_feeding=None, observer_lock=None)
            if connection_observer.done():
                self._to_remove_connection_observers.append(connection_observer)
        if self._to_remove_connection_observers:
            for connection_observer in self._to_remove_connection_observers:
                self._observers_runner.remove(connection_observer)
            self._to_remove_connection_observers.clear()

    def _feed_loop(self, connection_observer, stop_feeding, observer_lock):
        start_time = connection_observer.life_status.start_time
        while True:
            if stop_feeding.is_set():
                # TODO: should it be renamed to 'cancelled' to be in sync with initial action?
                self.logger.debug("stopped {}".format(connection_observer))
                break
            if connection_observer.done():
                self.logger.debug("done {}".format(connection_observer))
                break
            current_time = time.time()
            run_duration = current_time - start_time
            # we need to check connection_observer.timeout at each round since timeout may change
            # during lifetime of connection_observer
            timeout = connection_observer.timeout
            if connection_observer.life_status.in_terminating:
                timeout = connection_observer.life_status.terminating_timeout
            if (timeout is not None) and (run_duration >= timeout):
                if connection_observer.life_status.in_terminating:
                    msg = "{} underlying real command failed to finish during {} seconds. It will be forcefully" \
                          " terminated".format(connection_observer, timeout)
                    self.logger.info(msg)
                    connection_observer.set_end_of_life()
                else:
                    with observer_lock:
                        time_out_observer(connection_observer,
                                          timeout=connection_observer.timeout,
                                          passed_time=run_duration,
                                          runner_logger=self.logger)
                        if connection_observer.life_status.terminating_timeout >= 0.0:
                            start_time = time.time()
                            connection_observer.life_status.in_terminating = True
                        else:
                            break
            else:
                self._call_on_inactivity(connection_observer=connection_observer, current_time=current_time)

            if self._in_shutdown:
                self.logger.debug("shutdown so cancelling {}".format(connection_observer))
                connection_observer.cancel()
            time.sleep(self._tick)  # give moler_conn a chance to feed observer

    def _call_on_inactivity(self, connection_observer, current_time):
        """
        Call on_inactivity on connection_observer if needed.

        :param connection_observer: ConnectionObserver object.
        :param current_time: current time in seconds.
        :return: None
        """
        life_status = connection_observer.life_status
        if (life_status.inactivity_timeout > 0.0) and (life_status.last_feed_time is not None):
            expected_feed_timeout = life_status.last_feed_time + life_status.inactivity_timeout
            if current_time > expected_feed_timeout:
                connection_observer.on_inactivity()
                connection_observer.life_status.last_feed_time = current_time
