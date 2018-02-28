# -*- coding: utf-8 -*-
# Copyright (C) 2018 Nokia
"""
Runner abstraction goal is to hide concurrency machinery used
to make it exchangeable (threads, asyncio, twisted, curio)
"""
import time
from concurrent.futures import ThreadPoolExecutor, wait
import logging
from abc import abstractmethod, ABCMeta
from six import add_metaclass

from moler.exceptions import ConnectionObserverTimeout

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
        return False  # exceptions (if any) should be reraised


class ThreadPoolExecutorRunner(ConnectionObserverRunner):
    def __init__(self, executor=None):
        """Create instance of ThreadPoolExecutorRunner class"""
        self._in_shutdown = False
        self._i_own_executor = False
        self.executor = executor
        self.logger = logging.getLogger('moler.runner.thread-pool')
        if executor is None:
            max_workers = (cpu_count() or 1) * 5  # fix for concurrent.futures  v.3.0.3  to have API of v.3.1.1 or above
            self.executor = ThreadPoolExecutor(max_workers=max_workers)
            self._i_own_executor = True

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
        self.logger.debug("starting {}".format(connection_observer))
        # TODO: check dependency - connection_observer.connection
        connection_observer_future = self.executor.submit(self.feed, connection_observer)
        return connection_observer_future

    def wait_for(self, connection_observer, connection_observer_future, timeout=10.0):
        """
        Await for connection_observer running in background or timeout.

        :param connection_observer: The one we are awaiting for.
        :param connection_observer_future: Future of connection-observer returned from submit().
        :param timeout: Max time (in float seconds) you want to await before you give up.
        :return:
        """
        self.logger.debug("awaiting {}".format(connection_observer))
        start_time = time.time()
        done, not_done = wait([connection_observer_future], timeout=timeout)
        if connection_observer_future in done:
            self.shutdown()
            result = connection_observer_future.result()
            self.logger.debug("{} returned {}".format(connection_observer, result))
            return result
        passed = time.time() - start_time
        connection_observer.cancel()
        connection_observer_future.cancel()
        self.shutdown()
        self.logger.debug("timeouted {}".format(connection_observer))
        raise ConnectionObserverTimeout(connection_observer, timeout, kind="await_done", passed_time=passed)

    def feed(self, connection_observer):  # active feeder - pulls for data
        """
        Feeds connection_observer by pulling data from connection and passing it to connection_observer.
        Should be called from background-processing of connection observer.
        """
        moler_conn = connection_observer.connection
        moler_conn.subscribe(connection_observer.data_received)
        while True:
            if connection_observer.done():
                moler_conn.unsubscribe(connection_observer.data_received)
                break
            if self._in_shutdown:
                connection_observer.cancel()
            time.sleep(0.01)  # give moler_conn a chance to feed observer
        return connection_observer.result()
