# -*- coding: utf-8 -*-

__author__ = 'Grzegorz Latuszek, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com'

import logging
import inspect
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


@add_metaclass(ABCMeta)
class ConnectionObserver(object):

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
        self.logger = logging.getLogger('moler.connection_observer')

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
            if is_async_caller():
                print("called from async code")
                return self
                # TODO: rethink it
                # hope someone is calling                await connection_observer()
                # what if not, if it is only                   connection_observer()
                # maybe just block it "for non-async usage" via exception
                # and force async code to use            await connection_observer
                # see also: https://hackernoon.com/controlling-python-async-creep-ec0a0f4b79ba
                # where same 'def fetch()' is used inside sync and async code
            return started_observer.await_done(*args, **kwargs)
        # TODO: raise ConnectionObserverFailedToStart

    def start(self, timeout=None, *args, **kwargs):
        """Start background execution of connection-observer."""
        if timeout:
            self.timeout = timeout
        self._validate_start(*args, **kwargs)
        self._is_running = True
        self._future = self.runner.submit(self)
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

    def __await__(self):
        """
        Await completion of connection-observer.

        Allows to use Python3 'await' syntax

        According to https://www.python.org/dev/peps/pep-0492/#await-expression
        it is a SyntaxError to use await outside of an async def function.
        :return:
        """
        # We may have already started connection_observer:
        #    connection_observer = SomeObserver()
        #    connection_observer.start()
        # then we await it via:
        #    result = await connection_observer
        # but above notation in terms of Python3 async code may also mean "start it and await completion", so it may look like:
        #    connection_observer = SomeObserver()
        #    result = await connection_observer
        if self._future is None:
            self.start()
        return self.runner.wait_for_iterator(self, self._future)

    def await_done(self, timeout=None):
        """Await completion of connection-observer."""
        if self.done():
            return self.result()
        if self._future is None:
            raise ConnectionObserverNotStarted(self)
        result = self.runner.wait_for(connection_observer=self, connection_observer_future=self._future,
                                      timeout=timeout)
        return result

    def cancel(self):
        """Cancel execution of connection-observer."""
        # TODO: call cancel on runner to stop background run of connection-observer
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

    def on_timeout(self):
        """ It's callback called by framework just before raise exception for Timeout """
        pass

    def extend_timeout(self, timedelta):
        prev_timeout = self.timeout
        self.timeout = self.timeout + timedelta
        msg = "Extended timeout from %.2f with delta %.2f to %.2f" % (prev_timeout, timedelta, self.timeout)
        self.runner.timeout_change(timedelta)
        self.logger.info(msg)

    @ClassProperty
    def observer_name(cls):
        name = camel_case_to_lower_case_underscore(cls.__name__)
        return name


# https://hackernoon.com/controlling-python-async-creep-ec0a0f4b79ba
def is_async_caller():
    """Figure out who's calling."""
    # Get the calling frame
    caller = inspect.currentframe().f_back.f_back
    # Pull the function name from FrameInfo
    func_name = inspect.getframeinfo(caller)[2]
    # Get the function object
    f = caller.f_locals.get(
        func_name,
        caller.f_globals.get(func_name)
    )
    # If there's any indication that the function object is a
    # coroutine, return True. inspect.iscoroutinefunction() should
    # be all we need, the rest are here to illustrate.
    # inspect has different checks depending on Python2/Python3
    iscoroutinefunction = inspect.iscoroutinefunction(f) if hasattr(inspect, "iscoroutinefunction") else False
    iscoroutine = inspect.iscoroutine(f) if hasattr(inspect, "iscoroutine") else False
    isawaitable = inspect.isawaitable(f) if hasattr(inspect, "isawaitable") else False
    isasyncgenfunction = inspect.isasyncgenfunction(f) if hasattr(inspect, "isasyncgenfunction") else False
    isasyncgen = inspect.isasyncgen(f) if hasattr(inspect, "isasyncgen") else False
    if any([iscoroutinefunction, inspect.isgeneratorfunction(f), iscoroutine, isawaitable,
            isasyncgenfunction, isasyncgen]):
        return True
    else:
        return False
