# -*- coding: utf-8 -*-
from abc import abstractmethod, ABCMeta
from six import add_metaclass

from moler.exceptions import NoResultSinceCancelCalled
from moler.exceptions import ResultNotAvailableYet
from moler.exceptions import ResultAlreadySet
from moler.runner import ThreadPoolExecutorRunner

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'


@add_metaclass(ABCMeta)
class ConnectionObserver(object):

    def __init__(self, connection=None):
        """
        Create instance of ConnectionObserver class
        :param connection: connection used to receive data awaited for
        """
        self.connection = connection
        self._is_running = False
        self._is_done = False
        self._is_cancelled = False
        self._result = None
        self._exception = None
        self.runner = ThreadPoolExecutorRunner()
        self._future = None

    def __str__(self):
        return '{}(id:{})'.format(self.__class__.__name__, id(self))

    def __repr__(self):
        cmd_str = self.__str__()
        connection_str = '<NO CONNECTION>'
        if self.connection:
            connection_str = repr(self.connection)
        return '{}, using {})'.format(cmd_str[:-1], connection_str)

    def __call__(self, *args, **kwargs):
        """
        Run connection-observer in foreground
        till it is done or timeouted
        """
        started_observer = self.start(*args, **kwargs)
        if started_observer:
            return started_observer.await_done(*args, **kwargs)
        # TODO: raise ConnectionObserverFailedToStart

    def start(self, *args, **kwargs):
        """Start background execution of connection-observer."""
        # ----------------------------------------------------------------------
        # We intentionally do not check if connection is open here.
        # In such case net result anyway will be failed/timeouted observer -
        # - so, user will need to investigate "why".
        # Checking connection state would benefit in early detection of:
        # "error condition - no chance to succeed since connection is closed".
        # However, drawback is a requirement on connection to have is_open() API
        # We choose minimalistic dependency over better troubleshooting support.
        # ----------------------------------------------------------------------
        # TODO: implement background run using runner
        self._is_running = True
        self._future = self.runner.submit(self)
        return self

    def await_done(self, timeout=10.0):
        """Await completion of connection-observer."""
        if self.done():
            return self.result()
        result = self.runner.wait_for(connection_observer=self, connection_observer_future=self._future, timeout=timeout)
        return result

    def cancel(self):
        """Cancel execution of connection-observer."""
        if self.cancelled() or self.done():
            return False
        self._is_done = True
        self._is_cancelled = True
        return True

    def cancelled(self):
        """Return True if the connection-observer has been cancelled."""
        return self._is_cancelled

    def running(self):
        """Return True if the connection-observer is currently executing."""
        if self.done() and self._is_running:
            self._is_running = False
        return self._is_running

    def done(self):
        """Return True if the connection-observer is already done."""
        return self._is_done

    def set_result(self, result):
        """Should be used to set final result"""
        if self.done():
            raise ResultAlreadySet(self)
        self._is_done = True
        self._result = result

    @abstractmethod
    def data_received(self, data):
        """
        Entry point where feeders pass data read from connection
        Here we perform data parsing to conclude in result setting
        """
        pass

    def set_exception(self, exception):
        """Should be used to indicate some failure during observation"""
        self._is_done = True
        self._exception = exception

    def result(self):
        """Retrieve final result of connection-observer"""
        if self.cancelled():
            raise NoResultSinceCancelCalled(self)
        if self._exception:
            raise self._exception
        if not self.done():
            raise ResultNotAvailableYet(self)
        return self._result
