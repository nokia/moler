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
import inspect
import time
import sys
import asyncio
import asyncio.tasks
import asyncio.futures
import threading
from moler.io.raw import TillDoneThread
from moler.exceptions import ConnectionObserverTimeout
from moler.exceptions import CommandTimeout
from moler.exceptions import MolerException
from moler.runner import ConnectionObserverRunner
from moler.helpers import instance_id


# following code thanks to:
# https://rokups.github.io/#!pages/python3-asyncio-sync-async.md


def _run_loop_till_condition(loop, condition_callable, timeout):
    start_time = time.time()
    passed = time.time() - start_time
    while passed < timeout:
        loop._run_once()  # let event loop do its job; havent found better way
        if condition_callable():
            return
        passed = time.time() - start_time
    raise asyncio.futures.TimeoutError()


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
            # if new_task and future.done() and not future.cancelled():
            # if future is @coroutine  like asyncio.wait_for
            # then it has no .done()
            if new_task and task.done() and not task.cancelled():
                # The coroutine raised a BaseException. Consume the exception
                # to not log a warning, the caller doesn't have access to the
                # local task.
                # future.exception()
                task.exception()
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
        feed_started = asyncio.Event()
        # if not event_loop.is_running():
        #     # following code ensures that feeding has started (subscription made in moler_conn)
        #     event_loop.run_until_complete(self._start_feeding(connection_observer, feed_started))

        self._start_feeding(connection_observer, feed_started)
        connection_observer_future = asyncio.ensure_future(self.feed(connection_observer, feed_started))

        # if event_loop.is_running():
        #     # ensure that feed() reached moler_conn-subscription point (feeding started)
        #     # run_nested_until_complete(asyncio.wait_for(feed_started.wait(), timeout=0.5))  # call asynchronous code from sync
        #     _run_loop_till_condition(event_loop, lambda: feed_started.is_set(), timeout=0.5)
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
                _run_loop_till_condition(event_loop, lambda: connection_observer.done(), timeout)
                result = connection_observer.result()

                # TODO: check:
                # result = run_nested_until_complete(asyncio.wait_for(connection_observer_future,
                #                                                     timeout=timeout))  # call asynchronous code from sync
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

        return connection_observer_future.__iter__()
        # Note: even if code is so simple we can't move it inside ConnectionObserver.__await__() since different runners
        # may provide different iterator implementing awaitable
        # Here we know, connection_observer_future is asyncio.Future (precisely asyncio.tasks.Task) and we know it has __await__() method.

    def _start_feeding(self, connection_observer, feed_started):
        """
        Start feeding connection_observer by establishing data-channel from connection to observer.
        """
        self.logger.debug("start feeding({})".format(connection_observer))
        moler_conn = connection_observer.connection
        self.logger.debug("subscribing for data {!r}".format(connection_observer))
        moler_conn.subscribe(connection_observer.data_received)
        self.logger.debug("feeding({}) started".format(connection_observer))
        feed_started.set()  # mark that we have passed connection-subscription-step

    async def feed(self, connection_observer, feed_started):
        """
        Feeds connection_observer by transferring data from connection and passing it to connection_observer.
        Should be called from background-processing of connection observer.
        """
        self.logger.debug("START OF feed({})".format(connection_observer))
        if not feed_started.is_set():
            self._start_feeding(connection_observer, feed_started)

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


class AsyncioEventThreadsafe(asyncio.Event):
    def set(self):
        logger = logging.getLogger('moler.runner.asyncio-in-thrd')
        # Get the calling frame
        caller = inspect.currentframe().f_back  #.f_back
        caller_caller = inspect.currentframe().f_back.f_back
        fr_info1 = inspect.getframeinfo(caller)
        fr_info2 = inspect.getframeinfo(caller_caller) if caller_caller else None
        # Pull the function name from FrameInfo
        func_name = fr_info1[2]
        func_name2 = fr_info2[2] if fr_info2 else "End-of-call-stack"

        logger.debug("AsyncioEventThreadsafe.set() called from {}() called from {}()\n{}\n{}".format(func_name, func_name2, fr_info1, fr_info2))
        self._loop.call_soon_threadsafe(super().set)

    def clear(self):
        self._loop.call_soon_threadsafe(super().clear)


class AsyncioInThreadRunner(AsyncioRunner):
    def __init__(self):
        """Create instance of AsyncioInThreadRunner class"""
        self._in_shutdown = False
        self._id = 0
        self.logger = logging.getLogger('moler.runner.asyncio-in-thrd:{}'.format(self._id))
        self._loop_thread = None
        self._loop = None
        self._loop_done = None  # asyncio.Event that stops loop and holding it thread
        self.logger.debug("created")
        atexit.register(self.shutdown)

    def _start_loop_thread(self):
        self._loop = asyncio.new_event_loop()
        self._loop_done = AsyncioEventThreadsafe(loop=self._loop)
        self._loop.set_debug(enabled=True)
        self._loop_done.clear()
        loop_started = threading.Event()
        self._loop_thread = TillDoneThread(target=self._start_loop,
                                           done_event=self._loop_done,
                                           kwargs={'loop': self._loop,
                                                   'loop_started': loop_started,
                                                   'loop_done': self._loop_done})
        self._loop_thread.start()
        # await loop thread to be really started
        start_timeout = 0.5
        if not loop_started.wait(timeout=start_timeout):
            err_msg = "Failed to start asyncio loop thread within {} sec".format(start_timeout)
            self._loop_done.set()
            raise MolerException(err_msg)
        self.logger.info("started new asyncio-in-thrd loop ...")

    def _start_loop(self, loop, loop_started, loop_done):
        self.logger.info("starting new asyncio-in-thrd loop ...")
        asyncio.set_event_loop(loop)
        loop_started.set()
        loop.run_until_complete(self._await_stop_loop(stop_event=loop_done))
        self.logger.info("... asyncio-in-thrd loop done")

    async def _await_stop_loop(self, stop_event):
        # stop_event may be set directly via self._loop_done.set()
        # or indirectly by TillDoneThread when python calls join on all active threads during python shutdown
        self.logger.info("will await stop_event ...")
        await stop_event.wait()
        self.logger.info("... await stop_event done")

    def shutdown(self):
        self.logger.debug("shutting down")
        self._in_shutdown = True  # will exit from feed()
        # TODO: should we await for feed to complete?
        # if self._loop_done:
        #     self._loop_done.set()  # will exit from loop and holding it thread

    def submit(self, connection_observer):
        """
        Submit connection observer to background execution.
        Returns Future that could be used to await for connection_observer done.
        """
        self._id = instance_id(connection_observer)
        self.logger = logging.getLogger('moler.runner.asyncio-in-thrd:{}'.format(self._id))
        self.logger.debug("go background: {!r}".format(connection_observer))

        # TODO: check dependency - connection_observer.connection

        if self._loop_thread is None:
            self._start_loop_thread()

        feed_started = threading.Event()

        # we are scheduling to other thread (so, can't use asyncio.ensure_future() )
        connection_observer_future = asyncio.run_coroutine_threadsafe(self.feed(connection_observer, feed_started), loop=self._loop)
        # run_coroutine_threadsafe returns future as concurrent.futures.Future() and not asyncio.Future
        # so, we can await it with timeout inside current thread

        # await feeder to be really started, feeder runs in other thread, so we await for cross-threads event
        start_timeout = 0.5
        if not feed_started.wait(timeout=start_timeout):
            err_msg = "Failed to start observer feeder within {} sec".format(start_timeout)
            exc = MolerException(err_msg)
            connection_observer.set_exception(exception=exc)
            self.logger.error(repr(exc))
            # we not only store exception inside observer-as-future
            # but we also wan't to break caller code as quickly as possible
            raise exc

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
                _run_loop_till_condition(event_loop, lambda: connection_observer.done(), timeout)
                result = connection_observer.result()

                # TODO: check:
                # result = run_nested_until_complete(asyncio.wait_for(connection_observer_future,
                #                                                     timeout=timeout))  # call asynchronous code from sync
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

# monkeypatch()
