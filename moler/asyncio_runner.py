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
import threading
import time

from moler.exceptions import MolerTimeout
from moler.exceptions import MolerException
from moler.exceptions import WrongUsage
from moler.helpers import instance_id
from moler.io.raw import TillDoneThread
from moler.runner import ConnectionObserverRunner, result_for_runners, time_out_observer


def thread_secure_get_event_loop():
    """
    Need securing since asyncio.get_event_loop() when called from new thread
    may raise sthg like:
    RuntimeError: There is no current event loop in thread 'Thread-3'
    It is so since MainThread has preinstalled loop but other threads must
    setup own loop by themselves.

    :return: loop of current thread
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError as err:
        if "no current event loop in thread" in str(err):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        else:
            raise

    return loop


class AsyncioRunner(ConnectionObserverRunner):
    def __init__(self, logger_name='moler.runner.asyncio'):
        """Create instance of AsyncioRunner class"""
        self._in_shutdown = False
        self._id = instance_id(self)
        self.logger = logging.getLogger('{}:{}'.format(logger_name, self._id))
        self.logger.debug("created {}:{}".format(self.__class__.__name__, self._id))
        self._submitted_futures = []
        atexit.register(self.shutdown)

    def shutdown(self):
        self.logger.debug("shutting down")
        self._in_shutdown = True  # will exit from feed()
        # event_loop = thread_secure_get_event_loop()
        # if not event_loop.is_closed():
        #     remaining_tasks = asyncio.gather(*self._submitted_futures, return_exceptions=True)
        #     remaining_tasks.cancel()
        #     # cleanup_selected_tasks(tasks2cancel=self._submitted_futures, loop=event_loop, logger=self.logger)
        self._submitted_futures = []

    def submit(self, connection_observer):
        """
        Submit connection observer to background execution.
        Returns Future that could be used to await for connection_observer done.
        """
        self.logger.debug("go background: {!r}".format(connection_observer))

        # TODO: check dependency - connection_observer.connection

        feed_started = asyncio.Event(loop=thread_secure_get_event_loop())

        # Our submit consists of two steps:
        # 1. _start_feeding() which establishes data path from connection to observer
        # 2. starting "background feed" task handling native future bound to connection_observer
        #                               native future here is asyncio.Task
        # We could await here (before returning from submit()) for "background feed" to be really started.
        # However, for asyncio runner it is technically impossible (or possible but tricky)
        # since to be able to await for 'feed_started' asyncio.Event we need to give control back to events loop.
        # And the only way to do it is to return from this method since it is raw method (not 'async def' which
        # would allow for 'await' syntax)
        #
        # But by using the code of _start_feeding() we ensure that after submit() connection data could reach
        # data_received() of observer - as it would be "virtually running in background"
        # so, no data will be lost-for-observer between runner.submit() and runner.feed() really running
        #
        # Moreover, not waiting for "background feed" to be running (assuming tricky code) is in line
        # with generic scheme of any async-code: methods should be as quick as possible. Because async frameworks
        # operate inside single thread being inside method means "nothing else could happen". Nothing here may
        # mean for example "handling data of other connections", "handling other observers".
        #
        # duration of submit() is measured as around 0.0007sec (depends on machine).

        subscribed_data_receiver = self._start_feeding(connection_observer, feed_started)
        self.logger.debug("scheduling feed({})".format(connection_observer))
        connection_observer_future = asyncio.ensure_future(self.feed(connection_observer,
                                                                     feed_started,
                                                                     subscribed_data_receiver))
        self.logger.debug("runner submit() returning - future: {}:{}".format(instance_id(connection_observer_future),
                                                                             connection_observer_future))
        self._submitted_futures.append(connection_observer_future)
        return connection_observer_future

    def wait_for(self, connection_observer, connection_observer_future, timeout=None):
        """
        Await for connection_observer running in background or timeout.

        :param connection_observer: The one we are awaiting for.
        :param connection_observer_future: Future of connection-observer returned from submit().
        :param timeout: Max time (in float seconds) to await before give up. If None then taken from connection_observer
        :return:
        """
        self.logger.debug("go foreground: {!r} - await max. {} [sec]".format(connection_observer, timeout))
        start_time = time.time()
        event_loop = thread_secure_get_event_loop()

        try:
            # we might be already called from within running event loop
            # or we are just in synchronous code
            if event_loop.is_running():
                # wait_for() should not be called from 'async def'
                self._raise_wrong_usage_of_wait_for(connection_observer)
            else:
                event_loop.run_until_complete(asyncio.wait_for(connection_observer_future,
                                                               timeout=timeout))
        except asyncio.futures.CancelledError:
            self.logger.debug("canceled {}".format(connection_observer))
            connection_observer.cancel()
        except asyncio.futures.TimeoutError:
            passed = time.time() - start_time
            fired_timeout = timeout if timeout else connection_observer.timeout
            time_out_observer(connection_observer=connection_observer,
                              timeout=fired_timeout, passed_time=passed, kind="await_done")
        except Exception as err:
            self.logger.debug("{} raised {!r}".format(connection_observer, err))
            connection_observer.set_exception(err)
        finally:
            connection_observer_future.cancel()

        if connection_observer_future in self._submitted_futures:
            self._submitted_futures.remove(connection_observer_future)
        return None

    def _raise_wrong_usage_of_wait_for(self, connection_observer):
        import inspect  # don't import if never raising this exception
        (_, _, _, caller_name, _, _) = inspect.stack()[1]
        (_, _, _, caller_caller_name, _, _) = inspect.stack()[2]
        # Prefer to speak in observer API not runner API since user uses observers-API (runner is hidden)
        user_call_name = caller_caller_name if caller_caller_name == 'await_done' else caller_name
        err_msg = "Can't call {}() from 'async def' - it is blocking call".format(user_call_name)
        err_msg += "\n    observer = {}()".format(connection_observer.__class__.__name__)
        err_msg += "\n    observer.start()"
        err_msg += "\nconsider using:"
        err_msg += "\n    await observer"
        err_msg += "\ninstead of:"
        err_msg += "\n    observer.await_done()"
        self.logger.error(msg=err_msg)
        raise WrongUsage(err_msg)

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

        # assuming that connection_observer.start() / runner.submit(connection_observer)
        # has already scheduled future via asyncio.ensure_future
        assert asyncio.futures.isfuture(connection_observer_future)

        return connection_observer_future.__iter__()
        # Note: even if code is so simple we can't move it inside ConnectionObserver.__await__() since different runners
        # may provide different iterator implementing awaitable
        # Here we know, connection_observer_future is asyncio.Future (precisely asyncio.tasks.Task)
        # and we know it has __await__() method.

    def _start_feeding(self, connection_observer, feed_started):
        """
        Start feeding connection_observer by establishing data-channel from connection to observer.
        """
        # we have following ending conditions:
        # 1) connection observer consuming data sets result      -> .done() == True
        # 2) connection observer consuming data sets exception   -> .done() == True
        # 3) connection observer is cancelled                    -> .done() == True
        # 4) connection observer times out                  ------> NOT HANDLED HERE (yet?)
        # 5) connection observer consuming data raises exception -> secured to .set_exception() here
        # 6) runner is in shutdown state
        #
        # main purpose of secure_data_received() is to progress observer-life by data
        #
        def secure_data_received(data):
            try:
                if connection_observer.done() or self._in_shutdown:
                    return  # even not unsubscribed secure_data_received() won't pass data to done observer
                connection_observer.data_received(data)

            except Exception as exc:  # TODO: handling stacktrace
                # observers should not raise exceptions during data parsing
                # but if they do so - we fix it
                connection_observer.set_exception(exc)
            finally:
                if connection_observer.done() and not connection_observer.cancelled():
                    if connection_observer._exception:
                        self.logger.debug("{} raised: {!r}".format(connection_observer, connection_observer._exception))
                    else:
                        self.logger.debug("{} returned: {}".format(connection_observer, connection_observer._result))

        moler_conn = connection_observer.connection
        self.logger.debug("subscribing for data {!r}".format(connection_observer))
        moler_conn.subscribe(secure_data_received)
        feed_started.set()  # mark that we have passed connection-subscription-step
        return secure_data_received  # to know what to unsubscribe

    async def feed(self, connection_observer, feed_started, subscribed_data_receiver):
        """
        Feeds connection_observer by transferring data from connection and passing it to connection_observer.
        Should be called from background-processing of connection observer.
        """
        connection_observer._log(logging.INFO, "{} started.".format(connection_observer.get_long_desc()))
        if not feed_started.is_set():
            subscribed_data_receiver = self._start_feeding(connection_observer, feed_started)

        await asyncio.sleep(0.005)  # give control back before we start processing
        start_time = time.time()

        moler_conn = connection_observer.connection
        try:
            while True:
                if connection_observer.done():
                    self.logger.debug("done {!r}".format(connection_observer))
                    break
                run_duration = time.time() - start_time
                # we need to check connection_observer.timeout at each round since timeout may change
                # during lifetime of connection_observer
                if (connection_observer.timeout is not None) and (run_duration >= connection_observer.timeout):
                    self.logger.debug("timed out {!r}".format(connection_observer))
                    time_out_observer(connection_observer,
                                      timeout=connection_observer.timeout,
                                      passed_time=run_duration)
                    break
                if self._in_shutdown:
                    self.logger.debug("shutdown so cancelling {!r}".format(connection_observer))
                    connection_observer.cancel()
                await asyncio.sleep(0.005)  # give moler_conn a chance to feed observer
            #
            # main purpose of feed() is to progress observer-life by time
            #             firing timeout should do: observer.set_exception(Timeout)
            #
            # second responsibility: subscribe, unsubscribe observer from connection (build/break data path)
            # third responsibility: react on external stop request via observer.cancel() or runner.shutdown()

            # There is no need to put observer's result/exception into future:
            # Future's goal is to feed observer (by data or time) - exiting future here means observer is already fed.
            #
            # Moreover, putting observer's exception here, in future, causes problem at asyncio shutdown:
            # we get logs like: "Task exception was never retrieved" with bunch of stacktraces.
            # That is correct behaviour of asyncio to not exit silently when future/task has gone wrong.
            # However, feed() task worked fine since it correctly handled observer's exception.
            # Another words - it is not feed's exception but observer's exception so, it should not be raised here.
            #
            return None

        except asyncio.CancelledError:
            self.logger.debug("cancelled {!r}.feed".format(self))
            raise  # need to reraise to inform "I agree for cancellation"

        finally:
            self.logger.debug("unsubscribing {!r}".format(connection_observer))
            moler_conn.unsubscribe(subscribed_data_receiver)  # stop feeding
            # feed_done.set()
            connection_observer._log(logging.INFO, "{} finished.".format(connection_observer.get_short_desc()))

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
        super(AsyncioInThreadRunner, self).__init__(logger_name='moler.runner.asyncio-in-thrd')
        # AsyncioLoopThread must be created from MainThread since it adds signal handlers
        # (AsyncioLoopThread needs unix watchers embeding signal handles used to stop subprocesses)
        get_asyncio_loop_thread()

    def shutdown(self):
        self.logger.debug("shutting down")
        self._in_shutdown = True  # will exit from feed()
        # event_loop = thread_secure_get_event_loop()
        # if not event_loop.is_closed():
        #     remaining_tasks = asyncio.gather(*self._submitted_futures, return_exceptions=True)
        #     remaining_tasks.cancel()
        #     # cleanup_selected_tasks(tasks2cancel=self._submitted_futures, loop=event_loop, logger=self.logger)
        #     self._submitted_futures = []

    def submit(self, connection_observer):
        """
        Submit connection observer to background execution.
        Returns Future that could be used to await for connection_observer done.
        """
        self.logger.debug("go background: {!r}".format(connection_observer))

        # TODO: check dependency - connection_observer.connection

        # Our submit consists of two steps:
        # 1. scheduling start_feeder() in asyncio dedicated thread via run_async_coroutine()
        # 2. scheduling "background feed" via asyncio.ensure_future()
        #    - internally it calls _start_feeding() which sets feed_started event
        #
        # Moreover, we await here (before returning from submit()) for "background feed" to be really started.
        # That is realized by 0.5sec timeout and awaiting for feed_started asyncio.Event.
        # It ensures that feed() coroutine is already running inside asyncio loop.
        # Such functionality is possible thanks to using thread.
        #
        # By using the code of _start_feeding() we ensure that after submit() connection data could reach
        # data_received() of observer. Another words, no data will be lost-for-observer after runner.submit().
        #
        # Consequence of waiting for "background feed" to be running is that submit is blocking call till feed() start.
        # Generic scheme of any async-code is: methods should be as quick as possible. Because async frameworks
        # operate inside single thread blocking call means "nothing else could happen". Nothing here may
        # mean for example "handling data of other connections", "handling other observers".
        # So, if we put observer with AsyncioInThreadRunner inside some event loop then that loop will block
        # for duration of submit() which is measured as around 0.01sec (depends on machine).
        #
        # That 0.01sec price we want to pay since we gain another benefit for that price.
        # If anything goes wrong and start_feeder() can't be completed in 0.5sec we will be at least notified
        # by MolerException.

        async def start_feeder():
            feed_started = asyncio.Event()
            self.logger.debug("scheduling feed({})".format(connection_observer))
            conn_observer_future = asyncio.ensure_future(self.feed(connection_observer,
                                                                   feed_started,
                                                                   subscribed_data_receiver=None))
            self.logger.debug("scheduled feed() - future: {}".format(conn_observer_future))
            await feed_started.wait()
            self.logger.debug("feed() started - future: {}:{}".format(instance_id(conn_observer_future),
                                                                      conn_observer_future))
            return conn_observer_future

        thread4async = get_asyncio_loop_thread()
        start_timeout = 0.5
        try:
            connection_observer_future = thread4async.run_async_coroutine(start_feeder(), timeout=start_timeout)
        except MolerTimeout:
            err_msg = "Failed to start observer feeder within {} sec".format(start_timeout)
            self.logger.error(err_msg)
            exc = MolerException(err_msg)
            connection_observer.set_exception(exception=exc)
            return None
        self.logger.debug("runner submit() returning - future: {}:{}".format(instance_id(connection_observer_future),
                                                                             connection_observer_future))
        return connection_observer_future

    def wait_for(self, connection_observer, connection_observer_future, timeout=None):
        """
        Await for connection_observer running in background or timeout.

        :param connection_observer: The one we are awaiting for.
        :param connection_observer_future: Future of connection-observer returned from submit().
        :param timeout: Max time (in float seconds) to await before give up. None - use connection_observer.timeout
        :return:
        """
        self.logger.debug("go foreground: {!r} - await max. {} [sec]".format(connection_observer, timeout))
        start_time = time.time()

        async def wait_for_connection_observer_done():
            result_of_future = await connection_observer_future  # feed() always returns None
            return result_of_future

        thread4async = get_asyncio_loop_thread()
        try:
            if thread_secure_get_event_loop().is_running():
                # wait_for() should not be called from 'async def'
                self._raise_wrong_usage_of_wait_for(connection_observer)

            # If we have have timeout=None then concurrent.futures will wait infinitely
            # and feed() inside asyncio-loop will work on connection_observer.timeout
            #
            # If timeout is given then it defines max timeout (from "now") that concurrent.futures
            # may use to shorten lifetime of feed().
            # In such case we have concurrent.futures and asyncio race here - race about timeouts.
            thread4async.run_async_coroutine(wait_for_connection_observer_done(), timeout=timeout)
            # If feed() inside asyncio-loop handles timeout as first - we exit here.
            return None
        except MolerTimeout:
            # If run_async_coroutine() times out - we follow from here.
            pass
        except concurrent.futures.CancelledError:
            connection_observer.cancel()
            return None
        except Exception as err:
            err_msg = "{} raised {!r}".format(connection_observer, err)
            self.logger.debug(err_msg)
            if connection_observer._exception != err:
                connection_observer.set_exception(err)
            return None  # will be reraised during call to connection_observer.result()
        finally:
            # protect against leaking coroutines
            if not connection_observer_future.done():
                async def conn_observer_fut_cancel():
                    connection_observer_future.cancel()
                thread4async.start_async_coroutine(conn_observer_fut_cancel())

        # handle timeout
        passed = time.time() - start_time
        fired_timeout = timeout if timeout else connection_observer.timeout
        time_out_observer(connection_observer=connection_observer,
                          timeout=fired_timeout, passed_time=passed, kind="await_done")
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
        # return result_for_runners(connection_observer)  # May raise too.   # Python > 3.3
        res = result_for_runners(connection_observer)
        raise StopIteration(res)  # Python 2 compatibility


def cleanup_remaining_tasks(loop, logger):
    # https://stackoverflow.com/questions/30765606/whats-the-correct-way-to-clean-up-after-an-interrupted-event-loop
    # https://medium.com/python-pandemonium/asyncio-coroutine-patterns-beyond-await-a6121486656f
    # Handle shutdown gracefully by waiting for all tasks to be cancelled
    all_tasks = [task for task in asyncio.Task.all_tasks(loop=loop)]
    not_done_tasks = [task for task in asyncio.Task.all_tasks(loop=loop) if not task.done()]
    if not_done_tasks:
        logger.info("cancelling all remaining tasks")
        # NOTE: following code cancels all tasks - possibly not ours as well

        cleanup_selected_tasks(tasks2cancel=not_done_tasks, loop=loop, logger=logger)


def cleanup_selected_tasks(tasks2cancel, loop, logger):
    logger.debug("tasks to cancel: {}".format(tasks2cancel))
    remaining_tasks = asyncio.gather(*tasks2cancel, loop=loop, return_exceptions=True)
    remaining_tasks.add_done_callback(lambda t: loop.stop())
    remaining_tasks.cancel()

    # Keep the event loop running until it is either destroyed or all
    # tasks have really terminated
    loop.run_until_complete(remaining_tasks)


class AsyncioLoopThread(TillDoneThread):
    def __init__(self, name="Asyncio"):
        self.logger = logging.getLogger('moler.asyncio-loop-thrd')
        self.ev_loop = asyncio.new_event_loop()

        # to allow subprocesses running in "subthread"
        # otherwise we get error:
        # RuntimeError: Cannot add child handler, the child watcher does not have a loop attached
        # This is because unix watchers embed signal handles used to stop subprocesses
        #
        # https://stackoverflow.com/questions/28915607/does-asyncio-support-running-a-subprocess-from-a-non-main-thread/28917653#28917653
        #   When asyncio starts subprocess it need to be notified by subproc finish event.
        #   Unfortunately in Unix systems the generic way to do it is catching SIG_CHLD signal.
        #   Python interpreter can process signals only in main thread.
        # answer by: https://stackoverflow.com/users/3454879/andrew-svetlov
        #
        asyncio.get_child_watcher().attach_loop(self.ev_loop)

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

    def join(self, timeout=None):
        """
        Closing asyncio loop must be done from MainThread
        to allow for removing signal handlers
        """
        super(AsyncioLoopThread, self).join(timeout=timeout)
        self.logger.info("finished asyncio-loop-thrd ...")
        self.logger.info("closing events loop ...")
        self.ev_loop.close()
        self.logger.info("... asyncio loop closed")

    def _start_loop(self, loop, loop_started, loop_done):
        asyncio.set_event_loop(loop)
        try:
            self.logger.info("starting new asyncio loop ...")
            loop.run_until_complete(self._await_stop_loop(loop_started=loop_started, stop_event=loop_done))
            # cleanup_remaining_tasks(loop=loop, logger=self.logger)
        finally:
            self.logger.info("asyncio loop is done ...")

    async def _await_stop_loop(self, loop_started, stop_event):
        # stop_event may be set directly via self._loop_done.set()
        # or indirectly by TillDoneThread when python calls join on all active threads during python shutdown
        self.logger.info("will await loop stop_event ...")
        loop_started.set()
        await stop_event.wait()
        self.logger.info("... await loop stop_event done")

    def run_async_coroutine(self, coroutine_to_run, timeout):
        """Start coroutine in dedicated thread and await its result with timeout"""
        start_time = time.time()
        coro_future = self.start_async_coroutine(coroutine_to_run)
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

    def start_async_coroutine(self, coroutine_to_run):
        """Start coroutine in dedicated thread, don't await its result"""
        # we are scheduling to other thread (so, can't use asyncio.ensure_future() )
        self.logger.debug("scheduling {} into {}".format(coroutine_to_run, self.ev_loop))
        coro_future = asyncio.run_coroutine_threadsafe(coroutine_to_run, loop=self.ev_loop)
        return coro_future


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
