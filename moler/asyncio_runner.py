# -*- coding: utf-8 -*-
# Copyright (C) 2018 Nokia
"""
Asyncio Runner
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import asyncio
import asyncio.futures
import asyncio.tasks
import atexit
import concurrent.futures
import logging
import sys
import threading
import time

from moler.exceptions import CommandTimeout
from moler.exceptions import MolerTimeout
from moler.exceptions import ConnectionObserverTimeout
from moler.exceptions import MolerException
from moler.helpers import instance_id
from moler.io.raw import TillDoneThread
from moler.runner import ConnectionObserverRunner, result_for_runners


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
        except Exception:
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

                result = result_for_runners(connection_observer)

                # TODO: check:
                # result = run_nested_until_complete(asyncio.wait_for(connection_observer_future,
                #                                                     timeout=timeout))  # call asynchronous code from sync
            else:
                result = event_loop.run_until_complete(asyncio.wait_for(connection_observer_future,
                                                                        timeout=timeout))
        except asyncio.futures.CancelledError:
            self.logger.debug("canceled {}".format(connection_observer))
            connection_observer.cancel()
        except asyncio.futures.TimeoutError:
            passed = time.time() - start_time
            self.logger.debug("timed out {}".format(connection_observer))
            connection_observer.on_timeout()
            if hasattr(connection_observer, "command_string"):
                err = CommandTimeout(connection_observer, timeout, kind="await_done", passed_time=passed)
            else:
                err = ConnectionObserverTimeout(connection_observer, timeout, kind="await_done", passed_time=passed)
            connection_observer.set_exception(err)
        except Exception as err:
            self.logger.debug("{} raised {!r}".format(connection_observer, err))
            connection_observer.set_exception(err)
        else:
            self.logger.debug("{} returned {}".format(connection_observer, result))
        finally:
            moler_conn = connection_observer.connection
            moler_conn.unsubscribe(connection_observer.data_received)
        return None

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
        self.logger.debug("feed subscribing for data {!r}".format(connection_observer))
        moler_conn.subscribe(connection_observer.data_received)
        self.logger.debug("feeding({}) started".format(connection_observer))
        feed_started.set()  # mark that we have passed connection-subscription-step

    async def feed(self, connection_observer, feed_started):
        """
        Feeds connection_observer by transferring data from connection and passing it to connection_observer.
        Should be called from background-processing of connection observer.
        """
        connection_observer._log(logging.INFO, "{} started.".format(connection_observer.get_long_desc()))
        self.logger.debug("START OF feed({})".format(connection_observer))
        if not feed_started.is_set():
            self._start_feeding(connection_observer, feed_started)

        await asyncio.sleep(0.01)  # give control back before we start processing
        moler_conn = connection_observer.connection
        try:
            while True:
                if connection_observer.done():
                    self.logger.debug(
                        "feed done & unsubscribing {!r}".format(connection_observer))
                    moler_conn.unsubscribe(connection_observer.data_received)  # stop feeding
                    break
                if self._in_shutdown:
                    self.logger.debug(
                        "feed: shutdown so cancelling {!r}".format(connection_observer))
                    connection_observer.cancel()
                await asyncio.sleep(0.01)  # give moler_conn a chance to feed observer
            self.logger.debug("END   OF feed({})".format(connection_observer))
            try:
                result = result_for_runners(connection_observer)
                self.logger.debug("feed returning result: {}".format(result))
                return result
            except Exception as err:
                self.logger.debug("feed raising: {!r}".format(err))
                raise
            finally:
                connection_observer._log(logging.INFO, "{} finished.".format(connection_observer.get_short_desc()))

        except asyncio.CancelledError:
            self.logger.debug("Cancelled {!r}.feed".format(self))
            raise  # need to reraise to inform "I agree for cancellation"

    def timeout_change(self, timedelta):
        pass


class AsyncioEventThreadsafe(asyncio.Event):
    def set(self):
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
        self.logger.debug("created AsyncioInThreadRunner:{}".format(id(self)))
        atexit.register(self.shutdown)

    def _start_loop_thread(self):
        self._loop = asyncio.new_event_loop()
        self.logger.debug("created loop 4 thread: {}:{}".format(id(self._loop), self._loop))
        self._loop_done = AsyncioEventThreadsafe(loop=self._loop)
        self._loop.set_debug(enabled=True)
        self._loop_done.clear()
        loop_started = threading.Event()
        self._loop_thread = TillDoneThread(target=self._start_loop,
                                           done_event=self._loop_done,
                                           kwargs={'loop': self._loop,
                                                   'loop_started': loop_started,
                                                   'loop_done': self._loop_done})
        self.logger.debug("created thread {} with loop {}:{}".format(self._loop_thread, id(self._loop), self._loop))
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
        if self._loop_done:
            self._loop_done.set()  # will exit from loop and holding it thread

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
            try:
                self._start_loop_thread()
            except MolerException as err_msg:
                self.logger.error(err_msg)
                connection_observer.set_exception(err_msg)
                return None

        feed_started = threading.Event()

        # async def start_feeder():
        #     feed_started = asyncio.Event()
        #     self.logger.debug("scheduling feed()")
        #     connection_observer_future = asyncio.ensure_future(self.feed(connection_observer, feed_started))
        #     self.logger.debug("scheduled feed() - future: {}".format(connection_observer_future))
        #     await feed_started.wait()
        #     self.logger.debug("feed() started - future: {}".format(connection_observer_future))
        #     return connection_observer_future
        #
        # thread4async = get_asyncio_loop_thread()
        # start_timeout = 0.5
        # try:
        #     connection_observer_future = thread4async.run_async_coroutine(start_feeder(), timeout=start_timeout)
        # except MolerTimeout:

        # we are scheduling to other thread (so, can't use asyncio.ensure_future() )
        connection_observer_future = asyncio.run_coroutine_threadsafe(self.feed(connection_observer, feed_started), loop=self._loop)
        # run_coroutine_threadsafe returns future as concurrent.futures.Future() and not asyncio.Future
        # so, we can await it with timeout inside current thread

        # await feeder to be really started, feeder runs in other thread, so we await for cross-threads event
        start_timeout = 0.5
        if not feed_started.wait(timeout=start_timeout):
            err_msg = "Failed to start observer feeder within {} sec".format(start_timeout)
            self.logger.error(err_msg)
            exc = MolerException(err_msg)
            connection_observer.set_exception(exception=exc)
            return None
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
        remain_time = connection_observer.timeout
        check_timeout_from_observer = True
        wait_tick = 0.1
        if timeout:
            remain_time = timeout
            check_timeout_from_observer = False
            wait_tick = remain_time
        while remain_time > 0.0:
            done, _ = concurrent.futures.wait([connection_observer_future], timeout=wait_tick)
            if connection_observer_future in done:
                try:
                    result = result_for_runners(connection_observer_future)
                    self.logger.debug("{} returned {}".format(connection_observer, result))
                except Exception as err:
                    self.logger.debug("{} raised {!r}".format(connection_observer, err))
                return None
            if check_timeout_from_observer:
                timeout = connection_observer.timeout
            remain_time = timeout - (time.time() - start_time)
        moler_conn = connection_observer.connection
        moler_conn.unsubscribe(connection_observer.data_received)
        passed = time.time() - start_time
        self.logger.debug("timeouted {}".format(connection_observer))
        connection_observer.cancel()
        connection_observer_future.cancel()
        connection_observer.on_timeout()
        if hasattr(connection_observer, "command_string"):
            exception = CommandTimeout(connection_observer, timeout, kind="await_done", passed_time=passed)
        else:
            exception = ConnectionObserverTimeout(connection_observer, timeout, kind="await_done", passed_time=passed)
        connection_observer.set_exception(exception)
        return None

    def wait_for_iterator(self, connection_observer, connection_observer_future):
        """
        Version of wait_for() intended to be used by Python3 to implement iterable/awaitable object.

        Note: we don't have timeout parameter here. If you want to await with timeout please do use timeout machinery
        of selected parallelism.

        :param connection_observer: The one we are awaiting for.
        :param connection_observer_future: Future of connection-observer returned from submit().
        :return: iterator
        """
        self.logger.debug("returning iterator for {}".format(connection_observer))
        while not connection_observer_future.done():
            yield None
        # return result_for_runners(connection_observer_future)  # May raise too.   # Python > 3.3
        res = result_for_runners(connection_observer_future)
        raise StopIteration(res)  # Python 2 compatibility

# monkeypatch()


class AsyncioLoopThread(TillDoneThread):
    def __init__(self, name="Asyncio"):
        self.logger = logging.getLogger('moler.asyncio-loop-thrd')
        self.ev_loop = asyncio.new_event_loop()
        self.ev_loop.set_debug(enabled=True)

        self.logger.debug("created asyncio loop: {}:{}".format(id(self.ev_loop), self.ev_loop))
        self.ev_loop_done = AsyncioEventThreadsafe(loop=self.ev_loop)
        self.ev_loop_done.clear()
        self.ev_loop_started = threading.Event()

        super(AsyncioLoopThread, self).__init__(target=self._start_loop,
                                                done_event=self.ev_loop_done,
                                                kwargs={'loop': self.ev_loop,
                                                        'loop_started': self.ev_loop_started,
                                                        'loop_done': self.ev_loop_done})
        # Thread-3  -->  [Thread, 3]
        name_parts = self.name.split('-')
        self.name = "{}-{}".format(name, name_parts[-1])
        self.logger.debug("created thread {} for asyncio loop".format(self))

    def start(self):
        """
        We wan't this method to not return before it ensures
        that thread and it's enclosed loop are really running.
        """
        super(AsyncioLoopThread, self).start()
        # await loop thread to be really started
        start_timeout = 0.5
        if not self.ev_loop_started.wait(timeout=start_timeout):
            err_msg = "Failed to start asyncio loop thread within {} sec".format(start_timeout)
            self.ev_loop_done.set()
            raise MolerException(err_msg)
        self.logger.info("started new asyncio-loop-thrd ...")

    def _start_loop(self, loop, loop_started, loop_done):
        self.logger.info("starting new asyncio loop ...")
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._await_stop_loop(loop_started=loop_started, stop_event=loop_done))
        self.logger.info("... asyncio loop done")

    async def _await_stop_loop(self, loop_started, stop_event):
        # stop_event may be set directly via self._loop_done.set()
        # or indirectly by TillDoneThread when python calls join on all active threads during python shutdown
        self.logger.info("will await loop stop_event ...")
        loop_started.set()
        await stop_event.wait()
        self.logger.info("... await loop stop_event done")

    def run_async_coroutine(self, coroutine_to_run, timeout):
        start_time = time.time()
        # we are scheduling to other thread (so, can't use asyncio.ensure_future() )
        self.logger.debug("scheduling {} into {}".format(coroutine_to_run, self.ev_loop))
        coro_future = asyncio.run_coroutine_threadsafe(coroutine_to_run, loop=self.ev_loop)
        # run_coroutine_threadsafe returns future as concurrent.futures.Future() and not asyncio.Future
        # so, we can await it with timeout inside current thread
        try:
            coro_result = coro_future.result(timeout=timeout)
            self.logger.debug("scheduled {} returned {}".format(coroutine_to_run, coro_result))
            return coro_result
        except concurrent.futures.TimeoutError:
            passed = time.time() - start_time
            raise MolerTimeout(timeout=timeout,
                               kind="run_async_coroutine({})".format(coroutine_to_run),
                               passed_time=passed)
        except concurrent.futures.CancelledError:
            raise


_asyncio_loop_thread = None
_asyncio_loop_thread_lock = threading.Lock()


def get_asyncio_loop_thread():
    logger = logging.getLogger('moler.asyncio-loop-thrd')
    with _asyncio_loop_thread_lock:
        global _asyncio_loop_thread
        if _asyncio_loop_thread is None:
            logger.debug(">>> >>> found _asyncio_loop_thread as {}".format(_asyncio_loop_thread))

            logger.debug(">>> >>> will create thread {}".format(_asyncio_loop_thread))
            new_loop_thread = AsyncioLoopThread()
            logger.debug(">>> >>> AsyncioLoopThread() --> {}".format(new_loop_thread))
            new_loop_thread.start()
            logger.debug(">>> >>> started {}".format(new_loop_thread))
            _asyncio_loop_thread = new_loop_thread
    logger.debug(">>> >>> returning {}".format(_asyncio_loop_thread))
    return _asyncio_loop_thread
