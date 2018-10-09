# -*- coding: utf-8 -*-

__author__ = 'Grzegorz Latuszek, Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'

import logging
from abc import abstractmethod, ABCMeta

from six import add_metaclass

from moler.exceptions import ConnectionObserverNotStarted
from moler.exceptions import ConnectionObserverTimeout
from moler.exceptions import NoConnectionProvided
from moler.exceptions import NoResultSinceCancelCalled
from moler.exceptions import ResultAlreadySet
from moler.exceptions import ResultNotAvailableYet
from moler.helpers import ClassProperty
from moler.helpers import camel_case_to_lower_case_underscore
from moler.helpers import instance_id
from moler.runner import ThreadPoolExecutorRunner
import threading


@add_metaclass(ABCMeta)
class ConnectionObserver(object):
    _not_raised_exceptions = list()  # list of dict: "exception" and "time"
    _exceptions_lock = threading.Lock()

    def __init__(self, connection=None, runner=None):
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
        self.runner = runner if runner else ThreadPoolExecutorRunner()
        self._future = None
        self.timeout = 7
        self.device_logger = logging.getLogger('moler.{}'.format(self.get_logger_name()))
        self.logger = logging.getLogger('moler.connection.{}'.format(self.get_logger_name()))

    def __str__(self):
        return '{}(id:{})'.format(self.__class__.__name__, instance_id(self))

    def __repr__(self):
        cmd_str = self.__str__()
        connection_str = '<NO CONNECTION>'
        if self.connection:
            connection_str = repr(self.connection)
        return '{}, using {})'.format(cmd_str[:-1], connection_str)

    def __call__(self, timeout=None, *args, **kwargs):
        """
        Run connection-observer in foreground
        till it is done or timeouted
        """
        if timeout:
            self.timeout = timeout
        started_observer = self.start(timeout, *args, **kwargs)
        if started_observer:
            return started_observer.await_done(*args, **kwargs)
        # TODO: raise ConnectionObserverFailedToStart

    def get_logger_name(self):
        if self.connection and hasattr(self.connection, "name"):
            return self.connection.name
        else:
            return self.__class__.__name__

    def start(self, timeout=None, *args, **kwargs):
        """Start background execution of connection-observer."""
        if timeout:
            self.timeout = timeout
        self._validate_start(*args, **kwargs)
        self._is_running = True
        self._future = self.runner.submit(self)
        if self._future is None:
            self._is_running = False
        return self

    def _validate_start(self, *args, **kwargs):
        # check base class invariants first
        if not self.connection:
            # only if we have connection we can expect some data on it
            # at the latest "just before start" we need connection
            raise NoConnectionProvided(self)
        # ----------------------------------------------------------------------
        # We intentionally do not check if connection is open here.
        # In such case net result anyway will be failed/timeouted observer -
        # - so, user will need to investigate "why".
        # Checking connection state would benefit in early detection of:
        # "error condition - no chance to succeed since connection is closed".
        # However, drawback is a requirement on connection to have is_open() API
        # We choose minimalistic dependency over better troubleshooting support.
        # ----------------------------------------------------------------------
        if self.timeout <= 0.0:
            raise ConnectionObserverTimeout(self, self.timeout, "before run", "timeout is not positive value")

    def await_done(self, timeout=None):
        """Await completion of connection-observer."""
        if self.done():
            return self.result()
        if self._future is None:
            raise ConnectionObserverNotStarted(self)
        self.runner.wait_for(connection_observer=self, connection_observer_future=self._future,
                             timeout=timeout)

        return self.result()

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
        if self._exception:
            self._log(logging.DEBUG, "'{}.{}' has overwritten exception. From '{}.{}' to '{}.{}'.".format(
                self.__class__.__module__,
                self.__class__.__name__,
                self.exception.__class__.__module__,
                self.exception.__class__.__name__,
                exception.__class__.__module__,
                exception.__class__.__name__
            ))
            ConnectionObserver._remove_from_not_raised_exceptions(self._exception)
        self._exception = exception
        ConnectionObserver._append_to_not_raised_exceptions(exception)
        self._log(logging.INFO, "'{}.{}' has set exception '{}.{}'.".format(self.__class__.__module__,
                                                                            self.__class__.__name__,
                                                                            exception.__class__.__module__,
                                                                            exception.__class__.__name__))

    def result(self):
        """Retrieve final result of connection-observer"""
        if self._exception:
            if self._exception:
                ConnectionObserver._remove_from_not_raised_exceptions(self._exception)
            raise self._exception
        if self.cancelled():
            raise NoResultSinceCancelCalled(self)
        if not self.done():
            raise ResultNotAvailableYet(self)
        return self._result

    def on_timeout(self):
        """ It's callback called by framework just before raise exception for Timeout """
        pass

    def extend_timeout(self, timedelta):
        prev_timeout = self.timeout
        self.timeout = self.timeout + timedelta
        msg = "Extended timeout from %.2f with delta %.2f to %.2f" % (prev_timeout, timedelta, self.timeout)
        self.runner.timeout_change(timedelta)
        self._log(logging.INFO, msg)

    @ClassProperty
    def observer_name(cls):
        name = camel_case_to_lower_case_underscore(cls.__name__)
        return name

    @staticmethod
    def get_unraised_exceptions(remove=True):
        with ConnectionObserver._exceptions_lock:
            if remove:
                list_of_exceptions = ConnectionObserver._not_raised_exceptions
                ConnectionObserver._not_raised_exceptions = list()
                return list_of_exceptions
            else:
                list_of_exceptions = ConnectionObserver._not_raised_exceptions.copy()
                return list_of_exceptions

    @staticmethod
    def _append_to_not_raised_exceptions(exception):
        with ConnectionObserver._exceptions_lock:
            ConnectionObserver._not_raised_exceptions.append(exception)

    @staticmethod
    def _remove_from_not_raised_exceptions(exception):
        with ConnectionObserver._exceptions_lock:
            if exception in ConnectionObserver._not_raised_exceptions:
                ConnectionObserver._not_raised_exceptions.remove(exception)

    def get_long_desc(self):
        return "Observer '{}.{}'".format(self.__class__.__module__, self.__class__.__name__)

    def get_short_desc(self):
        return "Observer '{}.{}'".format(self.__class__.__module__, self.__class__.__name__)

    def _log(self, lvl, msg, extra=None):
        extra_params = {
            'log_name': self.get_logger_name()
        }

        if extra:
            extra_params.update(extra)

        self.logger.log(lvl, msg, extra=extra_params)
        self.device_logger.log(lvl, msg, extra=extra_params)
