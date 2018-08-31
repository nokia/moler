# -*- coding: utf-8 -*-
# Copyright (C) 2018 Nokia
"""
Asyncio Runner
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import atexit
import logging
import time
import sys
import asyncio
import asyncio.tasks
import asyncio.futures
from moler.exceptions import ConnectionObserverTimeout
from moler.exceptions import CommandTimeout
from moler.runner import ConnectionObserverRunner

# following code thanks to:
# https://rokups.github.io/#!pages/python3-asyncio-sync-async.md


def run_nested_until_complete(future, loop=None):
    """Run an event loop from within an executing task.

    This method will execute a nested event loop, and will not
    return until the passed future has completed execution. The
    nested loop shares the data structures of the main event loop,
    so tasks and events scheduled on the main loop will still
    execute while the nested loop is running.

    Semantically, this method is very similar to `yield from
    asyncio.wait_for(future)`, and where possible, that is the
    preferred way to block until a future is complete. The
    difference is that this method can be called from a
    non-coroutine function, even if that function was itself
    invoked from within a coroutine.
    """
    if loop is None:
        loop = asyncio.get_event_loop()

    loop._check_closed()
    if not loop.is_running():
        raise RuntimeError('Event loop is not running.')
    new_task = not isinstance(future, asyncio.futures.Future)
    task = asyncio.tasks.ensure_future(future, loop=loop)
    if new_task:
        # An exception is raised if the future didn't complete, so there
        # is no need to log the "destroy pending task" message
        task._log_destroy_pending = False
    while not task.done():
        try:
            loop._run_once()
        except Exception as err:
            if new_task and future.done() and not future.cancelled():
                # The coroutine raised a BaseException. Consume the exception
                # to not log a warning, the caller doesn't have access to the
                # local task.
                future.exception()
            raise
    return task.result()


def __reentrant_step(self, exc=None):
    containing_task = self.__class__._current_tasks.get(self._loop, None)
    try:
        __task_step(self, exc)
    finally:
        if containing_task:
            self.__class__._current_tasks[self._loop] = containing_task


def monkeypatch():
    global __task_step
    # Replace native Task, Future and _asyncio module implementations with pure-python ones. This is required in order
    # to access internal data structures of these classes.
    sys.modules['_asyncio'] = sys.modules['asyncio']
    asyncio.Task = asyncio.tasks._CTask = asyncio.tasks.Task = asyncio.tasks._PyTask
    asyncio.Future = asyncio.futures._CFuture = asyncio.futures.Future = asyncio.futures._PyFuture

    # Replace Task._step with reentrant version.
    __task_step = asyncio.tasks.Task._step
    asyncio.tasks.Task._step = __reentrant_step


class AsyncioRunner(ConnectionObserverRunner):
    def __init__(self):
        """Create instance of AsyncioRunner class"""
        self._in_shutdown = False
        self.logger = logging.getLogger('moler.runner.asyncio')
        self.logger.debug("created")
        atexit.register(self.shutdown)

    def shutdown(self):
        self.logger.debug("shutting down")
        self._in_shutdown = True  # will exit from feed()

    def submit(self, connection_observer):
        """
        Submit connection observer to background execution.
        Returns Future that could be used to await for connection_observer done.
        """
        self.logger.debug("go background: {!r}".format(connection_observer))

        # TODO: check dependency - connection_observer.connection

        # returned future is in reality task (task is derived from future)
        # moreover, such task is already scheduled for execution
        # CAUTION: If event loop is not running ensure_future() will mean nothing
        #          since there will be no one to start that scheduled coro.
        #          There will be just hope that someone will call wait_for() or event_loop.run_until_complete()
        #          but that might be too late - data from connection might be lost?
        #          NOT! since we have above subscription and data will pass into observer
        #          Not started feed async will just mean "there is no one to stop connection from
        #          feeding observer, connection will keep calling observer.data_received()
        #          so, either derived-observer.data_received() must have logic to ignore data after done
        #          or we should put moler_conn.subscribe() to small wrapper around observer.data_received()
        #          wrapper that unsubscribes after observer is done
        #          SOLUTION 2 ??? - async-in-thread runner
        event_loop = asyncio.get_event_loop()
        if not event_loop.is_running():
            # following code ensures that feeding has started (subscription made in moler_conn)
            event_loop.run_until_complete(self._start_feeding(connection_observer))

        feed_started = asyncio.Event()
        connection_observer_future = asyncio.ensure_future(self.feed(connection_observer, feed_started))

        if event_loop.is_running():
            # ensure that feed() reached moler_conn-subscription point (feeding started)
            run_nested_until_complete(asyncio.wait_for(feed_started.wait(), timeout=0.5))  # call asynchronous code from sync
        return connection_observer_future

    def wait_for(self, connection_observer, connection_observer_future, timeout=None):
        """
        Await for connection_observer running in background or timeout.

        :param connection_observer: The one we are awaiting for.
        :param connection_observer_future: Future of connection-observer returned from submit().
        :param timeout: Max time (in float seconds) you want to await before you give up. If None then taken from connection_observer
        :return:
        """
        self.logger.debug("go foreground: {!r} - await max. {} [sec]".format(connection_observer, timeout))
        start_time = time.time()
        if not timeout:
            timeout = connection_observer.timeout
        event_loop = asyncio.get_event_loop()

        try:
            # we might be already called from within running event loop
            # or we are just in synchronous code
            if event_loop.is_running():
                # we can't use await since we are not inside async def
                passed = time.time() - start_time
                while passed < timeout:
                    event_loop._run_once()  # let event loop do its job; havent found better way
                    if connection_observer.done():
                        return connection_observer.result()
                    passed = time.time() - start_time
                raise asyncio.futures.TimeoutError()
            else:
                result = event_loop.run_until_complete(asyncio.wait_for(connection_observer_future,
                                                                        timeout=timeout))
            self.logger.debug("{} returned {}".format(connection_observer, result))
            return result
        except asyncio.futures.CancelledError:
            self.logger.debug("canceled {}".format(connection_observer))
            connection_observer.cancel()
        except asyncio.futures.TimeoutError:
            passed = time.time() - start_time
            self.logger.debug("timeouted {}".format(connection_observer))
            connection_observer.on_timeout()
            if hasattr(connection_observer, "command_string"):
                err = CommandTimeout(connection_observer, timeout, kind="await_done", passed_time=passed)
            else:
                err = ConnectionObserverTimeout(connection_observer, timeout, kind="await_done", passed_time=passed)
            connection_observer.set_exception(err)

        moler_conn = connection_observer.connection
        moler_conn.unsubscribe(connection_observer.data_received)
        return connection_observer.result()  # will reraise correct exception

    # https://stackoverflow.com/questions/51029111/python-how-to-implement-a-c-function-as-awaitable-coroutine
    def wait_for_iterator(self, connection_observer, connection_observer_future):
        """
        Version of wait_for() intended to be used by Python3 to implement awaitable object.

        Note: we don't have timeout parameter here. If you want to await with timeout please do use asyncio machinery.
        For ex.:  await asyncio.wait_for(connection_observer, timeout=10)

        :param connection_observer: The one we are awaiting for.
        :param connection_observer_future: Future of connection-observer returned from submit().
        :return: iterator
        """
        self.logger.debug("go foreground: {!r}".format(connection_observer))

        # assuming that connection_observer.start() / runner.submit(connection_observer) has already scheduled future via asyncio.ensure_future
        assert asyncio.futures.isfuture(connection_observer_future)

        return connection_observer_future.__await__()
        # Note: even if code is so simple we can't move it inside ConnectionObserver.__await__() since different runners
        # may provide different iterator implementing awaitable
        # Here we know, connection_observer_future is asyncio.Future (precisely asyncio.tasks.Task) and we know it has __await__() method.

    async def _start_feeding(self, connection_observer):
        """
        Start feeding connection_observer by establishing data-channel from connection to observer.
        """
        self.logger.debug("start feeding({})".format(connection_observer))
        moler_conn = connection_observer.connection
        self.logger.debug("subscribing for data {!r}".format(connection_observer))
        moler_conn.subscribe(connection_observer.data_received)
        self.logger.debug("feeding({}) started".format(connection_observer))

    async def feed(self, connection_observer, feed_started):
        """
        Feeds connection_observer by transferring data from connection and passing it to connection_observer.
        Should be called from background-processing of connection observer.
        """
        self.logger.debug("START OF feed({})".format(connection_observer))
        await self._start_feeding(connection_observer)
        feed_started.set()  # mark that we have passed connection-subscription-step
        await asyncio.sleep(0.01)  # give control back before we start processing
        moler_conn = connection_observer.connection
        try:
            while True:
                if connection_observer.done():
                    self.logger.debug(
                        "done & unsubscribing {!r}".format(connection_observer))
                    moler_conn.unsubscribe(connection_observer.data_received)  # stop feeding
                    break
                if self._in_shutdown:
                    self.logger.debug(
                        "shutdown so cancelling {!r}".format(connection_observer))
                    connection_observer.cancel()
                await asyncio.sleep(0.01)  # give moler_conn a chance to feed observer
            self.logger.debug("returning result {}".format(connection_observer))
            self.logger.debug("END   OF feed({})".format(connection_observer))
            return connection_observer.result()
        except asyncio.CancelledError:
            self.logger.debug("Cancelled {!r}.feed".format(self))
            raise  # need to reraise to inform "I agree for cancellation"

    def timeout_change(self, timedelta):
        pass


monkeypatch()
