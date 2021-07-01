# -*- coding: utf-8 -*-

"""Wrapper for observer registered in ThreadedMolerConnection (old name: ObservableConnection)."""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2020-2021, Nokia'
__email__ = 'marcin.usielski@nokia.com'

from threading import Thread
from moler.config.loggers import TRACE
from moler.exceptions import CommandTimeout, ConnectionObserverTimeout
from moler.util.loghelper import log_into_logger
import time
import logging
from moler.util import tracked_thread

try:
    import queue
except ImportError:
    import Queue as queue  # For python 2


class ObserverThreadWrapper(object):
    """Wrapper for observer registered in ThreadedMolerConnection (old name: ObservableConnection)."""

    def __init__(self, observer, observer_self, logger):
        """
        Construct wrapper for observer.

        :param observer: observer to wrap.
        :param observer_self: self for observer if observer is method from object or None if observer is a function.
        :param logger: logger to log.
        """
        self._observer = observer
        self._observer_self = observer_self
        self._queue = queue.Queue()
        self._request_end = False
        self._timeout_for_get_from_queue = 1

        self._enable_loop_run_runner = True
        self._tick_for_runner = 0.01
        self.logger = logger
        self._connections_obsevers = list()
        self._to_remove_connection_observers = list()
        self._queue_for_connection_observers = queue.Queue()

        t = Thread(target=self._loop_for_observer)
        t.setDaemon(True)
        t.start()

        t = Thread(target=self._loop_for_runner)  # One thread for all commands and events.
        t.setDaemon(True)
        t.start()

    def feed(self, data, recv_time):
        """
        Put data here.

        :param data: data to put.
        :return: None
        """
        data_to_put = (data, recv_time)
        self._queue.put(data_to_put)
        self._queue_for_connection_observers.put(data_to_put)

    def request_stop(self):
        """
        Call if you want to stop feed observer.

        :return: None
        """
        self._request_end = True

    @tracked_thread.log_exit_exception
    def _loop_for_observer(self):
        """
        Loop to pass data (put by method feed) to observer.

        :return: None
        """
        logging.getLogger("moler_threads").debug("ENTER {}".format(self._observer))
        heartbeat = tracked_thread.report_alive()
        while self._request_end is False:
            if next(heartbeat):
                logging.getLogger("moler_threads").debug("ALIVE")
            try:
                data, timestamp = self._queue.get(True, self._timeout_for_get_from_queue)
                try:
                    self.logger.log(level=TRACE, msg=r'notifying {}({!r})'.format(self._observer, repr(data)))
                except ReferenceError:
                    self._request_end = True  # self._observer is no more valid.
                try:
                    if self._observer_self:
                        self._observer(self._observer_self, data, timestamp)
                    else:
                        self._observer(data, timestamp)
                except ReferenceError:
                    self._request_end = True  # self._observer is no more valid.
                except Exception:
                    self.logger.exception(msg=r'Exception inside: {}({!r})'.format(self._observer, repr(data)))
            except queue.Empty:
                pass  # No incoming data within self._timeout_for_get_from_queue
        self._observer = None
        self._observer_self = None

    def _loop_for_runner(self):
        while self._enable_loop_run_runner:
            if not self._connections_obsevers:
                time.sleep(self._tick_for_runner)
            self._feed_connection_observers()
            self._check_last_feed_connection_observers()
            self._check_timeout_connection_observers()
            for connection_observer in self._connections_obsevers:
                try:
                    pass
                except Exception as ex:
                    self.logger.exception(msg=r'Exception from "{}" when running checking: "{}" "{!r}".'.format(
                        connection_observer, ex, repr(ex)
                    ))
            self._remove_unnecessary_connection_observers()

    def _check_last_feed_connection_observers(self):
        """
        Call on_inactivity on connection_observer if needed.

        :return: None
        """
        current_time = time.time()
        for connection_observer in self._connections_obsevers:
            life_status = connection_observer.life_status
            if (life_status.inactivity_timeout > 0.0) and (life_status.last_feed_time is not None):
                expected_feed_timeout = life_status.last_feed_time + life_status.inactivity_timeout
                if current_time > expected_feed_timeout:
                    try:
                        connection_observer.on_inactivity()
                    except Exception as ex:
                        self.logger.exception(msg=r'Exception "{}" ("{}") inside: {} when on_inactivity.'.format(
                            ex, repr(ex), connection_observer))
                        connection_observer.set_exception(exception=ex)
                    finally:
                        connection_observer.life_status.last_feed_time = current_time

    def _check_timeout_connection_observers(self):
        for connection_observer in self._connections_obsevers:
            start_time = connection_observer.life_status.start_time
            current_time = time.time()
            run_duration = current_time - start_time
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
                    self._time_out_observer(connection_observer=connection_observer,
                                            timeout=connection_observer.timeout, passed_time=run_duration,
                                            runner_logger=self.logger)
                    if connection_observer.life_status.terminating_timeout >= 0.0:
                        connection_observer.life_status.start_time = time.time()
                        connection_observer.life_status.in_terminating = True

    def _timeout_observer(self, connection_observer, timeout, passed_time, runner_logger, kind="background_run"):
        """Set connection_observer status to timed-out"""
        if not connection_observer.life_status.was_on_timeout_called:
            connection_observer.life_status.was_on_timeout_called = True
            if not connection_observer.done():
                if connection_observer.is_command():
                    exception = CommandTimeout(connection_observer=connection_observer,
                                               timeout=timeout, kind=kind, passed_time=passed_time)
                else:
                    exception = ConnectionObserverTimeout(connection_observer=connection_observer,
                                                          timeout=timeout, kind=kind, passed_time=passed_time)
                # TODO: secure_data_received() may change status of connection_observer
                # TODO: and if secure_data_received() runs inside threaded connection - we have race
                connection_observer.set_exception(exception)

                connection_observer.on_timeout()

                observer_info = "{}.{}".format(connection_observer.__class__.__module__, connection_observer)
                timeout_msg = "has timed out after {:.2f} seconds.".format(passed_time)
                msg = "{} {}".format(observer_info, timeout_msg)

                # levels_to_go_up: extract caller info to log where .time_out_observer has been called from
                connection_observer._log(logging.INFO, msg, levels_to_go_up=2)
                log_into_logger(runner_logger, level=logging.DEBUG,
                                msg="{} {}".format(connection_observer, timeout_msg),
                                levels_to_go_up=1)

    def _remove_unnecessary_connection_observers(self):
        for connection_observer in self._connections_obsevers:
            if connection_observer.done():
                self._to_remove_connection_observers.append(connection_observer)
        if self._to_remove_connection_observers:
            for connection_observer in self._to_remove_connection_observers:
                self._connections_obsevers.remove(connection_observer)
            self._to_remove_connection_observers.clear()

    def _feed_connection_observers(self):
        try:
            data, timestamp = self._queue_for_connection_observers.get(True, self._tick_for_runner)
            feed_time = time.time()
            for connection_observer in self._connections_obsevers:
                try:
                    self.logger.log(level=TRACE, msg=r'notifying {}({!r})'.format(connection_observer, repr(data)))
                    connection_observer.data_received(data=data, recv_time=timestamp)
                except Exception as ex:
                    self.logger.exception(msg=r'Exception "{}" ("{}") inside: {} when processing ({!r})'.format(
                        ex, repr(ex), connection_observer, repr(data)))
                    connection_observer.set_exception(exception=ex)
                finally:
                    connection_observer.life_status.last_feed_time = feed_time
        except queue.Empty:
            pass  # No incoming data within self._tick_for_runner

    def submit(self, connection_observer):
        """
        Submit connection observer to background execution.
        """
        assert connection_observer.life_status.start_time > 0.0  # connection-observer lifetime should already been
        self._connections_obsevers.append(connection_observer)
        self._start_command(connection_observer=connection_observer)

    def _start_command(self, connection_observer):
        if connection_observer.is_command():
            connection_observer.send_command()
