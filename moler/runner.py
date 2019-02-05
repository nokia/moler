# -*- coding: utf-8 -*-
# Copyright (C) 2018 Nokia
"""
Runner abstraction goal is to hide concurrency machinery used
to make it exchangeable (threads, asyncio, twisted, curio)
"""

__author__ = 'Grzegorz Latuszek, Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'

import atexit
import concurrent.futures
import logging
import threading
import time
from abc import abstractmethod, ABCMeta
from concurrent.futures import ThreadPoolExecutor, wait

from six import add_metaclass

from moler.exceptions import CommandTimeout
from moler.exceptions import ConnectionObserverTimeout
from moler.exceptions import MolerException

# fix for concurrent.futures  v.3.0.3  to have API of v.3.1.1 or above
try:
    from multiprocessing import cpu_count
except ImportError:
    # some platforms don't have multiprocessing
    def cpu_count():
        """Workarround fix"""
        return None


@add_metaclass(ABCMeta)
class ConnectionObserverRunner(object):
    @abstractmethod
    def shutdown(self):
        """Cleanup used resources."""
        pass

    @abstractmethod
    def submit(self, connection_observer):
        """
        Submit connection observer to background execution.
        Returns Future that could be used to await for connection_observer done.
        """
        pass

    @abstractmethod
    def wait_for(self, connection_observer, connection_observer_future, timeout=10.0):
        """
        Await for connection_observer running in background or timeout.

        :param connection_observer: The one we are awaiting for.
        :param connection_observer_future: Future of connection-observer returned from submit().
        :param timeout: Max time (in float seconds) you want to await before you give up.
        :return:
        """
        pass

    @abstractmethod
    def feed(self, connection_observer):
        """
        Feeds connection_observer with data to let it become done.
        This is a place where runner is a glue between words of connection and connection-observer.
        Should be called from background-processing of connection observer.
        """
        pass

    @abstractmethod
    def timeout_change(self, timedelta):
        """
        Call this method to notify runner that timeout has been changed in observer
        :param timedelta: delta timeout in float seconds
        :return: Nothing
        """
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
        return False  # exceptions (if any) should be reraised


class CancellableFuture(object):
    def __init__(self, future, is_started, stop_running, is_done, stop_timeout=0.5):
        """
        Wrapper to allow cancelling already running concurrent.futures.Future

        Assumes that executor submitted function with following parameters
        fun(is_started, stop_running, is_done)
        and that such function correctly handles that events (threading.Event)

        :param future: wrapped instance of concurrent.futures.Future
        :param is_started: set when function started to run in thread
        :param stop_running: set externally to finish thread execution of function
        :param is_done: set when function finished running in thread
        :param stop_timeout: timeout to await is_done after setting stop_running
        """
        self._future = future
        self._is_started = is_started
        self._stop_running = stop_running
        self._stop_timeout = stop_timeout
        self._is_done = is_done

    def __getattr__(self, attr):
        """Make it proxy to embedded future"""
        attribute = getattr(self._future, attr)
        return attribute

    def cancel(self):
        if self.running():
            self._stop()

            # after exiting threaded-function future.state == FINISHED
            # we need to change it to PENDING to allow for correct cancel via concurrent.futures.Future
            with self._condition:
                self._future._state = concurrent.futures._base.PENDING

        return self._future.cancel()

    def _stop(self):
        self._stop_running.set()  # force threaded-function to exit
        if not self._is_done.wait(timeout=self._stop_timeout):
            err_msg = "Failed to stop thread-running function within {} sec".format(self._stop_timeout)
            # TODO: should we break current thread or just set this exception inside connection-observer
            #       (is it symetric to failed-start ?)
            # may cause leaking resources - no call to moler_conn.unsubscribe()
            raise MolerException(err_msg)


class ThreadPoolExecutorRunner(ConnectionObserverRunner):
    def __init__(self, executor=None):
        """Create instance of ThreadPoolExecutorRunner class"""
        self._in_shutdown = False
        self._i_own_executor = False
        self.executor = executor
        self.logger = logging.getLogger('moler.runner.thread-pool')
        self.logger.debug("created")
        atexit.register(self.shutdown)
        if executor is None:
            max_workers = (cpu_count() or 1) * 5  # fix for concurrent.futures  v.3.0.3  to have API of v.3.1.1 or above
            self.executor = ThreadPoolExecutor(max_workers=max_workers)
            self.logger.debug("created own executor {!r}".format(self.executor))
            self._i_own_executor = True
        else:
            self.logger.debug("reusing provided executor {!r}".format(self.executor))

    def shutdown(self):
        self.logger.debug("shutting down")
        self._in_shutdown = True  # will exit from feed() without stopping executor (since others may still use that executor)
        if self._i_own_executor:
            self.executor.shutdown()  # also stop executor since only I use it

    def submit(self, connection_observer):
        """
        Submit connection observer to background execution.
        Returns Future that could be used to await for connection_observer done.
        """
        self.logger.debug("go background: {!r}".format(connection_observer))
        # TODO: check dependency - connection_observer.connection
        feed_started = threading.Event()
        stop_feeding = threading.Event()
        feed_done = threading.Event()
        connection_observer_future = self.executor.submit(self.feed, connection_observer,
                                                          feed_started, stop_feeding, feed_done)
        # await feed thread to be really started
        start_timeout = 0.5
        if not feed_started.wait(timeout=start_timeout):
            err_msg = "Failed to start observer feeding thread within {} sec".format(start_timeout)
            self.logger.error(err_msg)
            exc = MolerException(err_msg)
            connection_observer.set_exception(exc)
            return None
        c_future = CancellableFuture(connection_observer_future, feed_started, stop_feeding, feed_done)
        return c_future

    def wait_for(self, connection_observer, connection_observer_future, timeout=None):
        """
        Await for connection_observer running in background or timeout.

        :param connection_observer: The one we are awaiting for.
        :param connection_observer_future: Future of connection-observer returned from submit().
        :param timeout: Max time (in float seconds) you want to await before you give up. If None then taken from connection_observer
        :return:
        """
        self.logger.debug("go foreground: {!r} - await max. {} [sec]".format(connection_observer, timeout))
        start_time = connection_observer.start_time
        remain_time = connection_observer.timeout
        check_timeout_from_observer = True
        wait_tick = 0.1
        if timeout:
            remain_time = timeout
            check_timeout_from_observer = False
            wait_tick = remain_time
        while remain_time > 0.0:
            done, not_done = wait([connection_observer_future], timeout=wait_tick)
            if connection_observer_future in done:
                connection_observer_future._stop()
                result = connection_observer_future.result()
                self.logger.debug("{} returned {}".format(connection_observer, result))
                return None
            if check_timeout_from_observer:
                timeout = connection_observer.timeout
            remain_time = timeout - (time.time() - start_time)

        # code below is for timed out observer
        passed = time.time() - start_time
        self.logger.debug("timed out {}".format(connection_observer))
        connection_observer_future.cancel()
        # TODO: rethink - on timeout we raise while on other exceptions we expect observers
        #       just to call  observer.set_exception() - so, no raise before calling observer.result()
        if connection_observer.is_command():
            exception = CommandTimeout(connection_observer, timeout, kind="await_done", passed_time=passed)
        else:
            exception = ConnectionObserverTimeout(connection_observer, timeout, kind="await_done", passed_time=passed)
        connection_observer.set_exception(exception)
        connection_observer.on_timeout()
        connection_observer._log(logging.INFO,
                                 "'{}.{}' has timed out after '{:.2f}' seconds.".format(
                                     connection_observer.__class__.__module__,
                                     connection_observer.__class__.__name__, time.time() - start_time))
        return None

    def feed(self, connection_observer, feed_started, stop_feeding, feed_done):
        """
        Feeds connection_observer by transferring data from connection and passing it to connection_observer.
        Should be called from background-processing of connection observer.
        """
        connection_observer._log(logging.INFO, "{} started.".format(connection_observer.get_long_desc()))
        moler_conn = connection_observer.connection

        def secure_data_received(data):
            try:
                connection_observer.data_received(data)
            except Exception as exc:  # TODO: handling stacktrace
                connection_observer.set_exception(exc)

        # start feeding connection_observer by establishing data-channel from connection to observer
        self.logger.debug("subscribing for data {!r}".format(connection_observer))
        moler_conn.subscribe(secure_data_received)

        if connection_observer.is_command():
            connection_observer.connection.sendline(connection_observer.command_string)
        feed_started.set()

        self._feed_loop(connection_observer, stop_feeding)

        self.logger.debug("unsubscribing {!r}".format(connection_observer))
        moler_conn.unsubscribe(secure_data_received)
        feed_done.set()

        connection_observer._log(logging.INFO, "{} finished.".format(connection_observer.get_short_desc()))
        self.logger.debug("returning result {}".format(connection_observer))
        return connection_observer.result()

    def timeout_change(self, timedelta):
        pass

    def _feed_loop(self, connection_observer, stop_feeding):
        while True:
            if stop_feeding.is_set():
                self.logger.debug("stopped {!r}".format(connection_observer))
                break
            if connection_observer.done():
                self.logger.debug("done {!r}".format(connection_observer))
                break
            if self._in_shutdown:
                self.logger.debug("shutdown so cancelling {!r}".format(connection_observer))
                connection_observer.cancel()
            time.sleep(0.01)  # give moler_conn a chance to feed observer
