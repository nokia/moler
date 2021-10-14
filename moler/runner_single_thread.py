# -*- coding: utf-8 -*-

"""
Moler implementation of Runner with single thread for MolerConnection: MolerConnectionForSingleThreadRunner.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2021, Nokia'
__email__ = 'marcin.usielski@nokia.com'


from threading import Lock
from moler.runner import ConnectionObserverRunner
from moler.exceptions import CommandTimeout
from moler.exceptions import ConnectionObserverTimeout
from moler.util.loghelper import log_into_logger
from moler.helpers import copy_list
import threading
import logging
import time

try:
    import queue
except ImportError:
    import Queue as queue  # For python 2


class RunnerSingleThread(ConnectionObserverRunner):

    """
    Moler implementation of Runner with single thread for MolerConnection: MolerConnectionForSingleThreadRunner.
    """

    _th_nr = 1

    def __init__(self):
        super(RunnerSingleThread, self).__init__()
        self.logger = logging.getLogger('moler.runner.connection-runner')
        self._connections_observers = list()
        self._copy_of_connections_observers = list()
        self._to_remove_connection_observers = list()
        self._stop_loop_runner = threading.Event()
        self._stop_loop_runner.clear()
        self._tick = 0.001
        self._in_shutdown = False
        self._loop_thread = threading.Thread(target=self._runner_loop,
                                             name="RunnerSingle-{}".format(RunnerSingleThread._th_nr)
                                             )
        RunnerSingleThread._th_nr += 1
        self._connection_observer_lock = Lock()
        self._loop_thread.setDaemon(True)
        self._loop_thread.start()

    def is_in_shutdown(self):
        """
        Call this method to check if runner is in shutdown mode.
        :return: Is in shutdown
        """
        return self._in_shutdown

    def submit(self, connection_observer):
        """
        Submit connection observer to background execution.
        Returns Future that could be used to await for connection_observer done.
        """
        assert connection_observer.life_status.start_time > 0.0  # connection-observer lifetime should already been
        self._add_connection_observer(connection_observer=connection_observer)

    def wait_for(self, connection_observer, connection_observer_future, timeout=10.0):
        """
        Await for connection_observer running in background or timeout.
        :param connection_observer: The one we are awaiting for.
        :param connection_observer_future: Future of connection-observer returned from submit(). Not used in this
        implementation!
        :param timeout: Max time (in float seconds) you want to await before you give up.
        :return: None
        """
        if connection_observer.done():
            self.logger.debug("go foreground: {} is already done".format(connection_observer))
        else:
            max_timeout = timeout
            observer_timeout = connection_observer.timeout
            # we count timeout from now if timeout is given; else we use .life.status.start_time and .timeout of
            # observer
            current_time = time.time()
            start_time = current_time if max_timeout else connection_observer.life_status.start_time
            await_timeout = max_timeout if max_timeout else observer_timeout
            if max_timeout:
                remain_time, msg = his_remaining_time("await max.", timeout=max_timeout, from_start_time=start_time)
            else:
                remain_time, msg = his_remaining_time("remaining", timeout=observer_timeout, from_start_time=start_time)
            self.logger.debug("go foreground: {} - {}".format(connection_observer, msg))
            connection_observer.life_status.start_time = start_time
            self._execute_till_eol(connection_observer=connection_observer,
                                   max_timeout=max_timeout,
                                   await_timeout=await_timeout,
                                   remain_time=remain_time)
            connection_observer.set_end_of_life()
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
        raise NotImplementedError()  # Planned for AsyncIO

    def feed(self, connection_observer):
        """
        Feeds connection_observer with data to let it become done.
        This is a place where runner is a glue between words of connection and connection-observer.
        Should be called from background-processing of connection observer. Left only for backward compatibility.
        """
        pass  # pylint: disable=unnecessary-pass
        # For backward compatibility only

    def timeout_change(self, timedelta):
        """
        Call this method to notify runner that timeout has been changed in observer
        :param timedelta: delta timeout in float seconds
        :return: None
        """
        pass  # pylint: disable=unnecessary-pass
        # For backward compatibility only.

    def shutdown(self):
        """
        Cleanup used resources.
        :return: None
        """
        self._in_shutdown = True
        observers = self._connections_observers
        self._connections_observers = list()
        self._stop_loop_runner.set()
        for connection_observer in observers:
            connection_observer.cancel()
            moler_connection = connection_observer.connection
            moler_connection.unsubscribe_connection_observer(connection_observer=connection_observer)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
        return False  # exceptions (if any) should be reraised

    def _add_connection_observer(self, connection_observer):
        """
        Add connection observer to the runner.
        :param connection_observer: the one to add.
        :return: None
        """
        with self._connection_observer_lock:
            if connection_observer not in self._connections_observers:
                moler_connection = connection_observer.connection
                moler_connection.subscribe_connection_observer(connection_observer=connection_observer)
                self._connections_observers.append(connection_observer)
                self._start_command(connection_observer=connection_observer)
                connection_observer.life_status.last_feed_time = time.time()

    def _execute_till_eol(self, connection_observer, max_timeout, await_timeout, remain_time):
        """
        Execute till end of life of connection_observer (done or timeout).
        :param connection_observer: Instance of ConnectionObserver (command or timeout).
        :param max_timeout: max timeout
        :param await_timeout: await timeout
        :param remain_time: remain time
        :return: True if done normally, False if timeout.
        """
        eol_remain_time = remain_time
        # either we wait forced-max-timeout or we check done-status each 0.1sec tick
        if eol_remain_time > 0.0:
            # future = connection_observer_future or connection_observer._future
            # assert future is not None
            if max_timeout:
                connection_observer_timeout = max_timeout
                check_timeout = False
            else:
                connection_observer_timeout = await_timeout
                check_timeout = True
            if connection_observer.done():
                return True
            was_done = self._wait_till_done(connection_observer=connection_observer,
                                            timeout=connection_observer_timeout,
                                            check_timeout=check_timeout)
            if was_done:
                return True
            self._prepare_for_time_out(connection_observer, timeout=await_timeout)
            if connection_observer.life_status.terminating_timeout > 0.0:
                connection_observer.life_status.in_terminating = True
                was_done = self._wait_till_done(connection_observer=connection_observer,
                                                timeout=connection_observer.life_status.terminating_timeout,
                                                check_timeout=check_timeout)
                if was_done:
                    return True

            self._wait_for_not_started_connection_observer_is_done(connection_observer=connection_observer)
        return False

    def _wait_till_done(self, connection_observer, timeout, check_timeout):
        """
        Wait till connection_obsertver is done.
        :param connection_observer: ConnectionObserver (command or event)
        :param timeout: timeout
        :param check_timeout: True to check timeout from connection_observer
        :return: True if done normally, False if timeout.
        """
        timeout_add = 0.1
        term_timeout = 0 if connection_observer.life_status.terminating_timeout is None else \
            connection_observer.life_status.terminating_timeout
        remain_time = timeout - (time.time() - connection_observer.life_status.start_time) + term_timeout + timeout_add
        while remain_time >= 0:
            if connection_observer.done():
                return True
            time.sleep(self._tick)
            if check_timeout:
                timeout = connection_observer.timeout
            term_timeout = 0 if connection_observer.life_status.terminating_timeout is None else \
                connection_observer.life_status.terminating_timeout
            remain_time = timeout - (time.time() - connection_observer.life_status.start_time) + term_timeout + \
                timeout_add
        return False

    def _wait_for_not_started_connection_observer_is_done(self, connection_observer):
        """
        Wait for not started connection observer (command or event) is done.
        :param connection_observer: ConnectionObserver (command or event)
        :return: None
        """
        # Have to wait till connection_observer is done with terminaing timeout.
        eol_remain_time = connection_observer.life_status.terminating_timeout
        start_time = time.time()
        while not connection_observer.done() and eol_remain_time > 0.0:
            time.sleep(self._tick)
            eol_remain_time = start_time + connection_observer.life_status.terminating_timeout - time.time()

    def _runner_loop(self):
        """
        Loop to check list of ConnectionObservers if anything to remove.
        :return:
        """
        while not self._stop_loop_runner.is_set():
            with self._connection_observer_lock:
                if self._copy_of_connections_observers != self._connections_observers:
                    self._copy_of_connections_observers = copy_list(self._connections_observers, deep_copy=False)
            # ConnectionObserver is feed by registering data_received in moler connection
            self._check_last_feed_connection_observers()
            self._check_timeout_connection_observers()
            self._remove_unnecessary_connection_observers()
            time.sleep(self._tick)

    def _check_last_feed_connection_observers(self):
        """
        Call on_inactivity on connection_observer if needed.
        :return: None
        """
        current_time = time.time()
        for connection_observer in self._copy_of_connections_observers:
            life_status = connection_observer.life_status
            if (life_status.inactivity_timeout > 0.0) and (life_status.last_feed_time is not None):
                expected_feed_timeout = life_status.last_feed_time + life_status.inactivity_timeout
                if current_time > expected_feed_timeout:
                    try:
                        connection_observer.on_inactivity()
                    except Exception as ex:
                        self.logger.exception(msg=r'Exception "{}" ("{}") inside: {} when on_inactivity.'.format(
                            ex, repr(ex), connection_observer))
                        connection_observer.set_exception(exception=ex)
                    finally:
                        connection_observer.life_status.last_feed_time = current_time

    def _check_timeout_connection_observers(self):
        """
        Check list of ConnectionObservers if any timeout.
        :return: None
        """
        for connection_observer in self._copy_of_connections_observers:
            start_time = connection_observer.life_status.start_time
            current_time = time.time()
            run_duration = current_time - start_time
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
                    self._timeout_observer(connection_observer=connection_observer,
                                           timeout=connection_observer.timeout, passed_time=run_duration,
                                           runner_logger=self.logger)
                    if connection_observer.life_status.terminating_timeout > 0.0:
                        connection_observer.life_status.start_time = time.time()
                        connection_observer.life_status.in_terminating = True
                    else:
                        connection_observer.set_end_of_life()

    def _prepare_for_time_out(self, connection_observer, timeout):
        """
        Prepare ConnectionObserver (command or event) for timeout.
        :param connection_observer: ConnectionObserver.
        :param timeout: timeout in seconds.
        :return: None
        """
        passed = time.time() - connection_observer.life_status.start_time
        self._timeout_observer(connection_observer=connection_observer,
                               timeout=timeout, passed_time=passed,
                               runner_logger=self.logger, kind="await_done")

    def _timeout_observer(self, connection_observer, timeout, passed_time, runner_logger, kind="background_run"):
        """
        Set connection_observer status to timed-out
        :param connection_observer: ConnectionObserver instance (command or event)
        :param timeout: timeout
        :param passed_time: passed time
        :param runner_logger: runner logger
        :param kind: Kind of running
        :return: None
        """
        if not connection_observer.life_status.was_on_timeout_called:
            connection_observer.life_status.was_on_timeout_called = True
            if not connection_observer.done():
                if connection_observer.is_command():
                    exception = CommandTimeout(connection_observer=connection_observer,
                                               timeout=timeout, kind=kind, passed_time=passed_time)
                else:
                    exception = ConnectionObserverTimeout(connection_observer=connection_observer,
                                                          timeout=timeout, kind=kind, passed_time=passed_time)
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

    def _remove_unnecessary_connection_observers(self):
        """
        Remove unnecessary ConnectionObservers from list to proceed.

        :return: None
        """
        for connection_observer in self._copy_of_connections_observers:
            if connection_observer.done():
                self._to_remove_connection_observers.append(connection_observer)
        if self._to_remove_connection_observers:
            with self._connection_observer_lock:
                for connection_observer in self._to_remove_connection_observers:
                    try:
                        self._connections_observers.remove(connection_observer)
                    except ValueError:
                        pass
                    moler_connection = connection_observer.connection
                    moler_connection.unsubscribe_connection_observer(connection_observer=connection_observer)
            self._to_remove_connection_observers = list()  # clear() is not available under old Pythons.

    def _start_command(self, connection_observer):
        """
        Srart command if connection_observer is an instance of a command. If an instance of event then do nothing.
        :param connection_observer: ConnectionObserver
        :return: None
        """
        if connection_observer.is_command():
            connection_observer.send_command()


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
