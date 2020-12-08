# -*- coding: utf-8 -*-
# Copyright (C) 2018-2020 Nokia
"""
Runner abstraction goal is to hide concurrency machinery used
to make it exchangeable (threads, asyncio, twisted, curio)
"""

__author__ = 'Grzegorz Latuszek, Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018-2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'

import atexit
import concurrent.futures
import logging
import threading
import time
from abc import abstractmethod, ABCMeta
from concurrent.futures import ThreadPoolExecutor, wait
from functools import partial

from six import add_metaclass

from moler.exceptions import CommandTimeout
from moler.exceptions import ConnectionObserverTimeout
from moler.exceptions import MolerException
from moler.exceptions import CommandFailure
from moler.util.loghelper import log_into_logger


@add_metaclass(ABCMeta)
class ConnectionObserverRunner(object):
    @abstractmethod
    def shutdown(self):
        """Cleanup used resources."""

    @abstractmethod
    def submit(self, connection_observer):
        """
        Submit connection observer to background execution.
        Returns Future that could be used to await for connection_observer done.
        """

    @abstractmethod
    def wait_for(self, connection_observer, connection_observer_future, timeout=10.0):
        """
        Await for connection_observer running in background or timeout.

        :param connection_observer: The one we are awaiting for.
        :param connection_observer_future: Future of connection-observer returned from submit().
        :param timeout: Max time (in float seconds) you want to await before you give up.
        :return:
        """

    @abstractmethod
    def wait_for_iterator(self, connection_observer, connection_observer_future):
        """
        Version of wait_for() intended to be used by Python3 to implement iterable/awaitable object.

        Note: we don't have timeout parameter here. If you want to await with timeout please do use timeout machinery
        of selected parallelism.

        :param connection_observer: The one we are awaiting for.
        :param connection_observer_future: Future of connection-observer returned from submit().
        :return: iterator
        """

    @abstractmethod
    def feed(self, connection_observer):
        """
        Feeds connection_observer with data to let it become done.
        This is a place where runner is a glue between words of connection and connection-observer.
        Should be called from background-processing of connection observer.
        """

    @abstractmethod
    def timeout_change(self, timedelta):
        """
        Call this method to notify runner that timeout has been changed in observer
        :param timedelta: delta timeout in float seconds
        :return: None
        """

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
        return False  # exceptions (if any) should be reraised


def time_out_observer(connection_observer, timeout, passed_time, runner_logger, kind="background_run"):
    """Set connection_observer status to timed-out"""
    if not connection_observer.life_status.was_on_timeout_called:
        connection_observer.life_status.was_on_timeout_called = True
        if not connection_observer.done():
            if hasattr(connection_observer, "command_string"):
                exception = CommandTimeout(connection_observer=connection_observer,
                                           timeout=timeout, kind=kind, passed_time=passed_time)
            else:
                exception = ConnectionObserverTimeout(connection_observer=connection_observer,
                                                      timeout=timeout, kind=kind, passed_time=passed_time)
            # TODO: secure_data_received() may change status of connection_observer
            # TODO: and if secure_data_received() runs inside threaded connection - we have race
            connection_observer.set_exception(exception)

            connection_observer.on_timeout()

            observer_info = "{}.{}".format(connection_observer.__class__.__module__, connection_observer)
            timeout_msg = "has timed out after {:.2f} seconds.".format(passed_time)
            msg = "{} {}".format(observer_info, timeout_msg)

            # levels_to_go_up: extract caller info to log where .time_out_observer has been called from
            connection_observer._log(logging.INFO, msg, levels_to_go_up=2)
            log_into_logger(runner_logger, level=logging.DEBUG,
                            msg="{} {}".format(connection_observer, timeout_msg),
                            levels_to_go_up=1)


def result_for_runners(connection_observer):
    """
    When runner takes result from connection-observer it should not
    modify ConnectionObserver._not_raised_exceptions

    :param connection_observer: observer to get result from
    :return: result or raised exception
    """
    if connection_observer._exception:
        raise connection_observer._exception
    return connection_observer.result()


class CancellableFuture(object):
    def __init__(self, future, observer_lock, stop_running, is_done, stop_timeout=0.5):
        """
        Wrapper to allow cancelling already running concurrent.futures.Future

        Assumes that executor submitted function with following parameters
        fun(stop_running, is_done)
        and that such function correctly handles that events (threading.Event)

        :param future: wrapped instance of concurrent.futures.Future
        :param stop_running: set externally to finish thread execution of function
        :param is_done: set when function finished running in thread
        :param stop_timeout: timeout to await is_done after setting stop_running
        """
        self._future = future
        self.observer_lock = observer_lock  # against threads race write-access to observer
        self._stop_running = stop_running
        self._stop_timeout = stop_timeout
        self._is_done = is_done

    def __getattr__(self, attr):
        """Make it proxy to embedded future"""
        attribute = getattr(self._future, attr)
        return attribute

    def __str__(self):
        """Make it proxy to embedded future"""
        f_str = str(self._future)
        return "CancellableFuture({})".format(f_str)

    def cancel(self, no_wait=False):
        """
        Cancel embedded future
        :param no_wait: if True - just set self._stop_running event to let thread exit loop
        :return:
        """
        if self.running():
            self._stop(no_wait)
            if no_wait:
                return True
            # after exiting threaded-function future.state == FINISHED
            # we need to change it to PENDING to allow for correct cancel via concurrent.futures.Future
            with self._condition:
                self._future._state = concurrent.futures._base.PENDING

        return self._future.cancel()

    def _stop(self, no_wait=False):
        self._stop_running.set()  # force threaded-function to exit
        if no_wait:
            return
        if not self._is_done.wait(timeout=self._stop_timeout):
            err_msg = "Failed to stop thread-running function within {} sec".format(self._stop_timeout)
            # TODO: should we break current thread or just set this exception inside connection-observer
            #       (is it symetric to failed-start ?)
            # may cause leaking resources - no call to moler_conn.unsubscribe()
            raise MolerException(err_msg)


class ThreadPoolExecutorRunner(ConnectionObserverRunner):
    def __init__(self, executor=None):
        """Create instance of ThreadPoolExecutorRunner class"""
        self._tick = 0.005  # Tick for sleep or partial timeout
        self._in_shutdown = False
        self._i_own_executor = False
        self._was_timeout_called = False
        self.executor = executor
        self.logger = logging.getLogger('moler.runner.thread-pool')
        self.logger.debug("created")
        atexit.register(self.shutdown)
        if executor is None:
            max_workers = 1000  # max 1000 threads in pool
            try:  # concurrent.futures  v.3.2.0 introduced prefix we like :-)
                self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix='ThrdPoolRunner')
            except TypeError as exc:
                if ('unexpected' in str(exc)) and ('thread_name_prefix' in str(exc)):
                    self.executor = ThreadPoolExecutor(max_workers=max_workers)
                else:
                    raise
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
        assert connection_observer.life_status.start_time > 0.0  # connection-observer lifetime should already been
        # started
        observer_timeout = connection_observer.timeout
        remain_time, msg = his_remaining_time("remaining", timeout=observer_timeout,
                                              from_start_time=connection_observer.life_status.start_time)
        self.logger.debug("go background: {!r} - {}".format(connection_observer, msg))
        # TODO: check dependency - connection_observer.connection

        # Our submit consists of two steps:
        # 1. _start_feeding() which establishes data path from connection to observer
        # 2. scheduling "background feed" via executor.submit()
        #
        # By using the code of _start_feeding() we ensure that after submit() connection data could reach
        # data_received() of observer - as it would be "virtually running in background"
        # Another words, no data will be lost-for-observer between runner.submit() and runner.feed() really running
        #
        # We do not await here (before returning from submit()) for "background feed" to be really started.
        # That is in sync with generic nature of threading.Thread - after thread.start() we do not have
        # running thread - it is user responsibility to await for threads switch.
        # User may check "if thread is running" via Thread.is_alive() API.
        # For concurrent.futures same is done via future.running() API.
        #
        # However, lifetime of connection_observer starts in connection_observer.start().
        # It gains it's own timer so that timeout is calculated from that connection_observer.life_status.start_time
        # That lifetime may start even before this submit() if observer is command and we have commands queue.
        #
        # As a corner case runner.wait_for() may timeout before feeding thread has started.

        stop_feeding = threading.Event()
        feed_done = threading.Event()
        observer_lock = threading.Lock()  # against threads race write-access to observer
        subscribed_data_receiver = self._start_feeding(connection_observer, observer_lock)
        connection_observer_future = self.executor.submit(self.feed, connection_observer,
                                                          subscribed_data_receiver,
                                                          stop_feeding, feed_done, observer_lock)
        if connection_observer_future.done():
            # most probably we have some exception during submit(); it should be stored inside future
            try:
                too_early_result = connection_observer_future.result()
                err_msg = "PROBLEM: future returned {} already in runner.submit()".format(too_early_result)
                self.logger.debug("go background: {} - {}".format(connection_observer, err_msg))
            except Exception as err:
                err_msg = "PROBLEM: future raised {!r} during runner.submit()".format(err)
                self.logger.warning("go background: {} - {}".format(connection_observer, err_msg))
                self.logger.exception(err_msg)
                raise

        finalizer = partial(self._feed_finish_callback,
                            connection_observer=connection_observer,
                            subscribed_data_receiver=subscribed_data_receiver,
                            feed_done=feed_done, observer_lock=observer_lock)
        connection_observer_future.add_done_callback(finalizer)

        c_future = CancellableFuture(connection_observer_future, observer_lock,
                                     stop_feeding, feed_done)
        connection_observer.life_status.last_feed_time = time.time()
        return c_future

    def wait_for(self, connection_observer, connection_observer_future, timeout=None):
        """
        Await for connection_observer running in background or timeout.

        :param connection_observer: The one we are awaiting for.
        :param connection_observer_future: Future of connection-observer returned from submit().
        :param timeout: Max time (in float seconds) you want to await before you give up. If None then taken from connection_observer
        :return:
        """
        # TODO: calculate remaining timeout before logging + done(result/exception) info
        if connection_observer.done():
            # 1. done() might mean "timed out" before future created (future is None)
            #    Observer lifetime started with its timeout clock so, it might timeout even before
            #    future created by runner.submit() - may happen for nonempty commands queue
            # 2. done() might mean "timed out" before future start
            #    Observer lifetime started with its timeout clock so, it might timeout even before
            #    connection_observer_future started - since future's thread might not get control yet
            # 3. done() might mean "timed out" before wait_for()
            #    wait_for() might be called so late after submit() that observer already "timed out"
            # 4. done() might mean have result or got exception
            #    wait_for() might be called so late after submit() that observer already got result/exception
            #
            # In all above cases we want to stop future if it is still running

            self.logger.debug("go foreground: {} is already done".format(connection_observer))
            self._cancel_submitted_future(connection_observer, connection_observer_future)
            return None

        max_timeout = timeout
        observer_timeout = connection_observer.timeout
        # we count timeout from now if timeout is given; else we use .life.status.start_time and .timeout of observer
        start_time = time.time() if max_timeout else connection_observer.life_status.start_time
        await_timeout = max_timeout if max_timeout else observer_timeout
        if max_timeout:
            remain_time, msg = his_remaining_time("await max.", timeout=max_timeout, from_start_time=start_time)
        else:
            remain_time, msg = his_remaining_time("remaining", timeout=observer_timeout, from_start_time=start_time)
        self.logger.debug("go foreground: {} - {}".format(connection_observer, msg))

        if connection_observer_future is None:
            end_of_life, remain_time = await_future_or_eol(connection_observer, remain_time, start_time, await_timeout,
                                                           self.logger)
            if end_of_life:
                return None
        if not self._execute_till_eol(connection_observer=connection_observer,
                                      connection_observer_future=connection_observer_future,
                                      max_timeout=max_timeout,
                                      await_timeout=await_timeout,
                                      remain_time=remain_time):
            # code below is to close ConnectionObserver and future objects
            self._end_of_life_of_future_and_connection_observer(connection_observer, connection_observer_future)
        return None

    def _execute_till_eol(self, connection_observer, connection_observer_future, max_timeout, await_timeout,
                          remain_time):
        eol_remain_time = remain_time
        # either we wait forced-max-timeout or we check done-status each 0.1sec tick
        if eol_remain_time > 0.0:
            future = connection_observer_future or connection_observer._future
            assert future is not None
            if max_timeout:
                done, not_done = wait([future], timeout=remain_time)
                if (future in done) or connection_observer.done():
                    self._cancel_submitted_future(connection_observer, future)
                    return True
                self._wait_for_time_out(connection_observer, connection_observer_future,
                                        timeout=await_timeout)
                if connection_observer.life_status.terminating_timeout > 0.0:
                    connection_observer.life_status.in_terminating = True
                    done, not_done = wait([future], timeout=connection_observer.life_status.terminating_timeout)
                    if (future in done) or connection_observer.done():
                        self._cancel_submitted_future(connection_observer, future)
                        return True
            else:
                while eol_remain_time > 0.0:
                    done, not_done = wait([future], timeout=self._tick)
                    if (future in done) or connection_observer.done():
                        self._cancel_submitted_future(connection_observer, future)
                        return True
                    already_passed = time.time() - connection_observer.life_status.start_time
                    eol_timeout = connection_observer.timeout + connection_observer.life_status.terminating_timeout
                    eol_remain_time = eol_timeout - already_passed
                    timeout = connection_observer.timeout
                    remain_time = timeout - already_passed
                    if remain_time <= 0.0:
                        self._wait_for_time_out(connection_observer, connection_observer_future,
                                                timeout=await_timeout)
                        if not connection_observer.life_status.in_terminating:
                            connection_observer.life_status.in_terminating = True
        else:
            self._wait_for_not_started_connection_observer_is_done(connection_observer=connection_observer)
        return False

    def _wait_for_not_started_connection_observer_is_done(self, connection_observer):
        # Have to wait till connection_observer is done with terminaing timeout.
        eol_remain_time = connection_observer.life_status.terminating_timeout
        start_time = time.time()
        while not connection_observer.done() and eol_remain_time > 0.0:
            time.sleep(self._tick)
            eol_remain_time = start_time + connection_observer.life_status.terminating_timeout - time.time()

    def _end_of_life_of_future_and_connection_observer(self, connection_observer, connection_observer_future):
        future = connection_observer_future or connection_observer._future
        if future:
            future.cancel(no_wait=True)
        connection_observer.set_end_of_life()

    @staticmethod
    def _cancel_submitted_future(connection_observer, connection_observer_future):
        future = connection_observer_future or connection_observer._future
        if future and (not future.done()):
            future.cancel(no_wait=True)

    def _wait_for_time_out(self, connection_observer, connection_observer_future, timeout):
        passed = time.time() - connection_observer.life_status.start_time
        future = connection_observer_future or connection_observer._future
        if future:
            with future.observer_lock:
                time_out_observer(connection_observer=connection_observer,
                                  timeout=timeout, passed_time=passed,
                                  runner_logger=self.logger, kind="await_done")
        else:
            # sorry, we don't have lock yet (it is created by runner.submit()
            time_out_observer(connection_observer=connection_observer,
                              timeout=timeout, passed_time=passed,
                              runner_logger=self.logger, kind="await_done")

    def wait_for_iterator(self, connection_observer, connection_observer_future):
        """
        Version of wait_for() intended to be used by Python3 to implement iterable/awaitable object.

        Note: we don't have timeout parameter here. If you want to await with timeout please do use timeout machinery
        of selected parallelism.

        :param connection_observer: The one we are awaiting for.
        :param connection_observer_future: Future of connection-observer returned from submit().
        :return: iterator
        """
        while not connection_observer_future.done():
            yield None
        # return result_for_runners(connection_observer)  # May raise too.   # Python > 3.3
        res = result_for_runners(connection_observer)
        raise StopIteration(res)  # Python 2 compatibility

    def _start_feeding(self, connection_observer, observer_lock):
        """
        Start feeding connection_observer by establishing data-channel from connection to observer.
        """

        def secure_data_received(data, timestamp):
            try:
                if connection_observer.done() or self._in_shutdown:
                    return  # even not unsubscribed secure_data_received() won't pass data to done observer
                with observer_lock:
                    connection_observer.data_received(data, timestamp)
                    connection_observer.life_status.last_feed_time = time.time()

            except Exception as exc:  # TODO: handling stacktrace
                # observers should not raise exceptions during data parsing
                # but if they do so - we fix it
                with observer_lock:
                    self.logger.warning("Unhandled exception from '{} 'caught by runner. '{}' : '{}'.".format(
                        connection_observer, exc, repr(exc)))
                    ex_msg = "Unexpected exception from {} caught by runner when processing data >>{}<< at '{}':" \
                             " >>>{}<<< -> repr: >>>{}<<<".format(connection_observer, data, timestamp, exc, repr(exc))
                    if connection_observer.is_command():
                        ex = CommandFailure(command=connection_observer, message=ex_msg)
                    else:
                        ex = MolerException(ex_msg)
                    connection_observer.set_exception(ex)
            finally:
                if connection_observer.done() and not connection_observer.cancelled():
                    if connection_observer._exception:
                        self.logger.debug("{} raised: {!r}".format(connection_observer, connection_observer._exception))
                    else:
                        self.logger.debug("{} returned: {}".format(connection_observer, connection_observer._result))

        moler_conn = connection_observer.connection
        self.logger.debug("subscribing for data {}".format(connection_observer))
        with observer_lock:
            moler_conn.subscribe(observer=secure_data_received,
                                 connection_closed_handler=connection_observer.connection_closed_handler)
            # after subscription we have data path so observer is started
            remain_time, msg = his_remaining_time("remaining", timeout=connection_observer.timeout,
                                                  from_start_time=connection_observer.life_status.start_time)
            connection_observer._log(logging.INFO, "{} started, {}".format(connection_observer.get_long_desc(), msg))
        if connection_observer.is_command():
            connection_observer.send_command()
        return secure_data_received  # to know what to unsubscribe

    def _stop_feeding(self, connection_observer, subscribed_data_receiver, feed_done, observer_lock):
        with observer_lock:
            if not feed_done.is_set():
                moler_conn = connection_observer.connection
                self.logger.debug("unsubscribing {}".format(connection_observer))
                moler_conn.unsubscribe(observer=subscribed_data_receiver,
                                       connection_closed_handler=connection_observer.connection_closed_handler)
                # after unsubscription we break data path so observer is finished
                remain_time, msg = his_remaining_time("remaining", timeout=connection_observer.timeout,
                                                      from_start_time=connection_observer.life_status.start_time)
                connection_observer._log(logging.INFO,
                                         "{} finished, {}".format(connection_observer.get_short_desc(), msg))
                feed_done.set()

    def _feed_finish_callback(self, future, connection_observer, subscribed_data_receiver, feed_done, observer_lock):
        """Callback attached to concurrent.futures.Future of submitted feed()"""
        self._stop_feeding(connection_observer, subscribed_data_receiver, feed_done, observer_lock)

    def feed(self, connection_observer, subscribed_data_receiver, stop_feeding, feed_done,
             observer_lock):
        """
        Feeds connection_observer by transferring data from connection and passing it to connection_observer.
        Should be called from background-processing of connection observer.
        """
        remain_time, msg = his_remaining_time("remaining", timeout=connection_observer.timeout,
                                              from_start_time=connection_observer.life_status.start_time)
        self.logger.debug("thread started  for {}, {}".format(connection_observer, msg))

        if not subscribed_data_receiver:
            subscribed_data_receiver = self._start_feeding(connection_observer, observer_lock)

        time.sleep(self._tick)  # give control back before we start processing

        self._feed_loop(connection_observer, stop_feeding, observer_lock)

        remain_time, msg = his_remaining_time("remaining", timeout=connection_observer.timeout,
                                              from_start_time=connection_observer.life_status.start_time)
        self.logger.debug("thread finished for {}, {}".format(connection_observer, msg))
        self._stop_feeding(connection_observer, subscribed_data_receiver, feed_done, observer_lock)
        return None

    def _feed_loop(self, connection_observer, stop_feeding, observer_lock):
        start_time = connection_observer.life_status.start_time
        while True:
            if stop_feeding.is_set():
                # TODO: should it be renamed to 'cancelled' to be in sync with initial action?
                self.logger.debug("stopped {}".format(connection_observer))
                break
            if connection_observer.done():
                self.logger.debug("done {}".format(connection_observer))
                break
            current_time = time.time()
            run_duration = current_time - start_time
            # we need to check connection_observer.timeout at each round since timeout may change
            # during lifetime of connection_observer
            timeout = connection_observer.timeout
            if connection_observer.life_status.in_terminating:
                timeout = connection_observer.life_status.terminating_timeout
            if (timeout is not None) and (run_duration >= timeout):
                if connection_observer.life_status.in_terminating:
                    msg = "{} underlying real command failed to finish during {} seconds. It will be forcefully" \
                          " terminated".format(connection_observer, timeout)
                    self.logger.info(msg)
                    connection_observer.set_end_of_life()
                else:
                    with observer_lock:
                        time_out_observer(connection_observer,
                                          timeout=connection_observer.timeout,
                                          passed_time=run_duration,
                                          runner_logger=self.logger)
                        if connection_observer.life_status.terminating_timeout >= 0.0:
                            start_time = time.time()
                            connection_observer.life_status.in_terminating = True
                        else:
                            break
            else:
                self._call_on_inactivity(connection_observer=connection_observer, current_time=current_time)

            if self._in_shutdown:
                self.logger.debug("shutdown so cancelling {}".format(connection_observer))
                connection_observer.cancel()
            time.sleep(self._tick)  # give moler_conn a chance to feed observer

    def _call_on_inactivity(self, connection_observer, current_time):
        """
        Call on_inactivity on connection_observer if needed.

        :param connection_observer: ConnectionObserver object.
        :param current_time: current time in seconds.
        :return: None
        """
        life_status = connection_observer.life_status
        if (life_status.inactivity_timeout > 0.0) and (life_status.last_feed_time is not None):
            expected_feed_timeout = life_status.last_feed_time + life_status.inactivity_timeout
            if current_time > expected_feed_timeout:
                connection_observer.on_inactivity()
                connection_observer.life_status.last_feed_time = current_time

    def timeout_change(self, timedelta):
        pass


# utilities to be used by runners


def his_remaining_time(prefix, timeout, from_start_time):
    """
    Calculate remaining time of "he" object assuming that "he" has .life_status.start_time attribute

    :param prefix: string to be used inside 'remaining time description'
    :param he: object to calculate remaining time for
    :param timeout: max lifetime of object
    :param from_start_time: start of lifetime for the object
    :return: remaining time as float and related description message
    """
    already_passed = time.time() - from_start_time
    remain_time = timeout - already_passed
    if remain_time < 0.0:
        remain_time = 0.0
    msg = "{} {:.3f} [sec], already passed {:.3f} [sec]".format(prefix, remain_time, already_passed)
    return remain_time, msg


def await_future_or_eol(connection_observer, remain_time, start_time, timeout, logger):
    # Observer lifetime started with its timeout clock
    # but setting connection_observer._future may be delayed by nonempty commands queue.
    # In such case we have to wait either for _future or timeout.
    end_of_life = False
    while (connection_observer._future is None) and (remain_time > 0.0):
        time.sleep(0.005)
        if connection_observer.done():
            logger.debug("{} is done before creating future".format(connection_observer))
            end_of_life = True
            break
        now = time.time()
        already_passed = now - start_time
        remain_time = timeout - already_passed
        observer_lifetime_passed = now - connection_observer.life_status.start_time
        remain_observer_lifetime = connection_observer.timeout + connection_observer.life_status.terminating_timeout\
            - observer_lifetime_passed
        # we timeout on earlier timeout (timeout or connection_observer.timeout)
        if remain_observer_lifetime <= 0.0:
            remain_time = 0.0
        if remain_time <= 0.0:
            logger.debug("{} timeout before creating future".format(connection_observer))

    return end_of_life, remain_time
