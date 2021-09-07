# -*- coding: utf-8 -*-

__author__ = 'Grzegorz Latuszek, Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018-2021 Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'

import logging
import threading
import time
from abc import abstractmethod, ABCMeta

from six import add_metaclass

from moler.exceptions import ConnectionObserverNotStarted
from moler.exceptions import ConnectionObserverTimeout
from moler.exceptions import NoConnectionProvided
from moler.exceptions import NoResultSinceCancelCalled
from moler.exceptions import ResultAlreadySet
from moler.exceptions import ResultNotAvailableYet
from moler.exceptions import WrongUsage
from moler.helpers import ClassProperty
from moler.helpers import camel_case_to_lower_case_underscore
from moler.helpers import instance_id
from moler.helpers import copy_list
from moler.util.connection_observer import exception_stored_if_not_main_thread
from moler.util.loghelper import log_into_logger
from moler.runner_factory import get_runner
from moler.command_scheduler import CommandScheduler
from moler.util.connection_observer_life_status import ConnectionObserverLifeStatus


@add_metaclass(ABCMeta)
class ConnectionObserver(object):
    _not_raised_exceptions = list()  # list of dict: "exception" and "time"
    _exceptions_lock = threading.Lock()

    def __init__(self, connection=None, runner=None):
        """
        Create instance of ConnectionObserver class
        :param connection: connection used to receive data awaited for
        """
        super(ConnectionObserver, self).__init__()
        self.life_status = ConnectionObserverLifeStatus()
        self.connection = connection
        self.runner = self._get_runner(runner=runner)
        self._result = None
        self._exception = None

        self._future = None

        self.device_logger = logging.getLogger('moler.{}'.format(self.get_logger_name()))
        self.logger = logging.getLogger('moler.connection.{}'.format(self.get_logger_name()))

    def _get_runner(self, runner):
        """

        :param runner: Runner
        :return: Runner instance
        """
        return_runner = runner
        if return_runner is None and self.connection is not None:
            return_runner = self.connection.get_runner()
        if return_runner is None:
            return_runner = get_runner()
        return return_runner

    def __str__(self):
        return '{}(id:{})'.format(self.__class__.__name__, instance_id(self))

    __base_str = __str__

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

        CAUTION: if you call it from asynchronous code (async def) you may block events loop for long time.
        You should rather await it via:
        result = await connection_observer
        or (to have timeout)
        result = await asyncio.wait_for(connection_observer, timeout=10)
        or you may delegate blocking call execution to separate thread,
        see: https://pymotw.com/3/asyncio/executors.html
        """
        self.start(timeout, *args, **kwargs)
        # started_observer = self.start(timeout, *args, **kwargs)
        # if started_observer:
        #     return started_observer.await_done(*args, **kwargs)
        return self.await_done()
        # TODO: raise ConnectionObserverFailedToStart

    @property
    def _is_done(self):
        return self.life_status.is_done

    @_is_done.setter
    def _is_done(self, value):
        self.life_status.is_done = value
        if value:
            CommandScheduler.dequeue_running_on_connection(connection_observer=self)

    @property
    def _is_cancelled(self):
        return self.life_status.is_cancelled

    @_is_cancelled.setter
    def _is_cancelled(self, value):
        self.life_status.is_cancelled = value

    @property
    def terminating_timeout(self):
        return self.life_status.terminating_timeout

    @terminating_timeout.setter
    def terminating_timeout(self, value):
        self.life_status.terminating_timeout = value

    @property
    def timeout(self):
        return self.life_status.timeout

    @timeout.setter
    def timeout(self, value):
        # levels_to_go_up=2 : extract caller info to log where .timeout=XXX has been called from
        self._log(logging.DEBUG, "Setting {} timeout to {} [sec]".format(ConnectionObserver.__base_str(self), value),
                  levels_to_go_up=2)
        self.life_status.timeout = value

    @property
    def start_time(self):
        return self.life_status.start_time

    def get_logger_name(self):
        if self.connection and hasattr(self.connection, "name"):
            return self.connection.name
        else:
            return self.__class__.__name__

    def start(self, timeout=None, *args, **kwargs):
        """Start background execution of connection-observer."""
        with exception_stored_if_not_main_thread(self):
            if timeout:
                self.timeout = timeout
            self._validate_start(*args, **kwargs)
            # After start we treat it as started even if it's underlying
            # parallelism machinery (threads, coroutines, ...) has not started yet
            # (thread didn't get control, coro didn't start in async-loop)
            # That is so, since observer lifetime starts with it's timeout-clock
            # and timeout is counted from calling observer.start()
            self.life_status._is_running = True
            self.life_status.start_time = time.time()
            # Besides not started parallelism machinery causing start-delay
            # we can have start-delay caused by commands queue on connection
            # (can't submit command to background-run till previous stops running)
            CommandScheduler.enqueue_starting_on_connection(connection_observer=self)
            # Above line will set self._future when it is possible to submit
            # observer to background-run (observer not command, or empty commands queue)
            # or setting self._future will be delayed by nonempty commands queue.
        return self

    def _validate_start(self, *args, **kwargs):
        # check base class invariants first
        if self.done():
            raise WrongUsage("You can't run same {} multiple times. It is already done.".format(self))
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

    def __iter__(self):  # Python 3.4 support - do we need it?
        """
        Implement iterator protocol to support 'yield from' in @asyncio.coroutine
        :return:
        """
        if self._future is None:
            self.start()
        assert self._future is not None
        return self.runner.wait_for_iterator(self, self._future)

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
        # but above notation in terms of Python3 async code may also mean "start it and await completion", so it may
        # look like:
        #    connection_observer = SomeObserver()
        #    result = await connection_observer
        return self.__iter__()

    def await_done(self, timeout=None):
        """
        Await completion of connection-observer.

        CAUTION: if you call it from asynchronous code (async def) you may block events loop for long time.
        You should rather await it via:
        result = await connection_observer
        or (to have timeout)
        result = await asyncio.wait_for(connection_observer, timeout=10)
        or you may delegate blocking call execution to separate thread,
        see: https://pymotw.com/3/asyncio/executors.html

        :param timeout:
        :return: observer result
        """
        if self.done():
            return self.result()
        with exception_stored_if_not_main_thread(self):
            if not self.life_status._is_running:
                raise ConnectionObserverNotStarted(self)
            # check if already is running
            self.runner.wait_for(connection_observer=self, connection_observer_future=self._future, timeout=timeout)
        return self.result()

    def cancel(self):
        """Cancel execution of connection-observer."""
        # TODO: call cancel on runner to stop background run of connection-observer
        if self.cancelled() or self.done():
            return False
        self._is_cancelled = True
        self._is_done = True
        return True

    def set_end_of_life(self):
        """
        Set end of life of object. Dedicated for runners only!

        :return: None
        """
        self._is_done = True

    def cancelled(self):
        """Return True if the connection-observer has been cancelled."""
        return self._is_cancelled

    def running(self):
        """Return True if the connection-observer is currently executing."""
        if self.done() and self.life_status._is_running:
            self.life_status._is_running = False
        return self.life_status._is_running

    def done(self):
        """Return True if the connection-observer is already done."""
        return self._is_done

    def set_result(self, result):
        """Should be used to set final result"""
        if self.done():
            raise ResultAlreadySet(self)
        self._result = result
        self._is_done = True

    def connection_closed_handler(self):
        """
        Called by Moler (ThreadedMolerConnection) when connection is closed.

        :return: None
        """
        if not self.done():
            connection_name = self.get_logger_name()
            msg = "'{}' is not done but connection '{}' is about to be closed.".format(self, connection_name)
            ex = WrongUsage(msg)
            self.set_exception(ex)
        self.cancel()

    @abstractmethod
    def data_received(self, data, recv_time):
        """
        Entry point where feeders pass data read from connection
        Here we perform data parsing to conclude in result setting.

        :param data: List of strings sent by device.
        :param recv_time: time stamp with the moment when the data was read from connection.  Time is given as
         datetime.datetime instance.
        :return: None.
        """

    def set_exception(self, exception):
        """
        Should be used to indicate some failure during observation.

        :param exception: Exception to set
        :return: None
        """
        self._set_exception_without_done(exception)
        self._is_done = True

    def _set_exception_without_done(self, exception):
        """
        Should be used to indicate some failure during observation. This method does not finish connection observer
        object!

        :param exception: exception to set
        :return: None
        """
        if self._is_done:
            self._log(logging.WARNING,
                      "Attempt to set exception {!r} on already done {}".format(exception, self),
                      levels_to_go_up=2)
            return
        ConnectionObserver._change_unraised_exception(new_exception=exception, observer=self)
        self._log(logging.INFO,
                  "{}.{} has set exception {!r}".format(self.__class__.__module__, self, exception),
                  levels_to_go_up=2)

    def result(self):
        """Retrieve final result of connection-observer"""
        with ConnectionObserver._exceptions_lock:
            ConnectionObserver._log_unraised_exceptions(self)
            if self._exception:
                exception = self._exception
                if exception in ConnectionObserver._not_raised_exceptions:
                    ConnectionObserver._not_raised_exceptions.remove(exception)
                raise exception
        if self.cancelled():
            raise NoResultSinceCancelCalled(self)
        if not self.done():
            raise ResultNotAvailableYet(self)
        return self._result

    def on_timeout(self):
        """Callback called when observer times out"""
        pass

    def is_command(self):
        """
        :return: True if instance of ConnectionObserver is a command. False if not a command.
        """
        return False

    def extend_timeout(self, timedelta):  # TODO: probably API to remove since we have runner tracking .timeout=XXX
        prev_timeout = self.timeout
        self.timeout = self.timeout + timedelta
        msg = "Extended timeout from %.2f with delta %.2f to %.2f" % (prev_timeout, timedelta, self.timeout)
        self.runner.timeout_change(timedelta)
        self._log(logging.INFO, msg)

    def on_inactivity(self):
        """
        Callback called when no data is received on connection within self.life_status.inactivity_timeout seconds

        :return: None
        """
        pass

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
                list_of_exceptions = copy_list(ConnectionObserver._not_raised_exceptions)
                return list_of_exceptions

    @staticmethod
    def _change_unraised_exception(new_exception, observer):
        with ConnectionObserver._exceptions_lock:
            old_exception = observer._exception
            ConnectionObserver._log_unraised_exceptions(observer)
            if old_exception:
                observer._log(logging.DEBUG,
                              "{} has overwritten exception. From {!r} to {!r}".format(
                                  observer,
                                  old_exception,
                                  new_exception,
                              ))
                if old_exception in ConnectionObserver._not_raised_exceptions:
                    ConnectionObserver._not_raised_exceptions.remove(old_exception)
                else:
                    observer._log(logging.DEBUG,
                                  "{}: cannot find exception {!r} in _not_raised_exceptions.".format(
                                      observer,
                                      old_exception,
                                  ))
                    ConnectionObserver._log_unraised_exceptions(observer)

            ConnectionObserver._not_raised_exceptions.append(new_exception)
            observer._exception = new_exception

    @staticmethod
    def _log_unraised_exceptions(observer):
        for i, item in enumerate(ConnectionObserver._not_raised_exceptions):
            observer._log(logging.DEBUG, "{:4d} NOT RAISED: {!r}".format(i + 1, item), levels_to_go_up=2)

    def get_long_desc(self):
        return "Observer '{}.{}'".format(self.__class__.__module__, self)

    def get_short_desc(self):
        return "Observer '{}.{}'".format(self.__class__.__module__, self)

    def _log(self, lvl, msg, extra=None, levels_to_go_up=1):
        extra_params = {
            'log_name': self.get_logger_name()
        }

        if extra:
            extra_params.update(extra)

        # levels_to_go_up=1 : extract caller info to log where _log() has been called from
        log_into_logger(self.logger, lvl, msg, extra=extra_params, levels_to_go_up=levels_to_go_up)
        log_into_logger(self.device_logger, lvl, msg, extra=extra_params, levels_to_go_up=levels_to_go_up)
