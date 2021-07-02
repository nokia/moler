from moler.threaded_moler_connection import ThreadedMolerConnection
from moler.runner import ThreadPoolExecutorRunner


__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2021, Nokia'
__email__ = 'marcin.usielski@nokia.com'


import weakref
import logging
import six
import time
from threading import Lock
from moler.abstract_moler_connection import AbstractMolerConnection
from moler.abstract_moler_connection import identity_transformation
from moler.config.loggers import RAW_DATA, TRACE
from moler.helpers import instance_id
from moler.observer_thread_wrapper import ObserverThreadWrapper
from moler.runner import ConnectionObserverRunner
from moler.exceptions import CommandTimeout
from moler.exceptions import ConnectionObserverTimeout

try:
    import queue
except ImportError:
    import Queue as queue  # For python 2


class RunnerWithThreadedMolerConnection(ThreadedMolerConnection):
    def __init__(self, how2send=None, encoder=identity_transformation, decoder=identity_transformation,
                 name=None, newline='\n', logger_name=""):
        """
        Create Connection via registering external-IO
        :param how2send: any callable performing outgoing IO
        :param encoder: callable converting data to bytes
        :param decoder: callable restoring data from bytes
        :param name: name assigned to connection
        :param logger_name: take that logger from logging
        Logger is retrieved by logging.getLogger(logger_name)
        If logger_name == "" - take logger "moler.connection.<name>"
        If logger_name is None - don't use logging
        """
        super(ThreadedMolerConnection, self).__init__(how2send, encoder, decoder, name=name, newline=newline,
                                                      logger_name=logger_name)
        self._connection_closed_handlers = dict()
        self._observer_wrappers = dict()
        self._observers_lock = Lock()
        self._observers_runner = list()
        self._to_remove_connection_observers = list()

    def data_received(self, data, recv_time):
        """
        Incoming-IO API:
        external-IO should call this method when data is received
        """
        if not self.is_open():
            return

        extra = {'transfer_direction': '<', 'encoder': lambda data: data.encode(encoding='utf-8', errors="replace")}
        self._log_data(msg=data, level=RAW_DATA,
                       extra=extra)

        decoded_data = self.decode(data)
        self._log_data(msg=decoded_data, level=logging.INFO,
                       extra=extra)

        self.notify_observers(decoded_data, recv_time)
        #self._check_observers_loop()

    def subscribe(self, observer, connection_closed_handler):
        """
        Subscribe for 'data-received notification'
        :param observer: function to be called to notify when data received.
        :param connection_closed_handler: callable to be called when connection is closed.
        """
        with self._observers_lock:
            self._log(level=TRACE, msg="subscribe({})".format(observer))
            observer_key, value = self._get_observer_key_value(observer)

            if observer_key not in self._observer_wrappers:
                self_for_observer, observer_reference = value
                self._observer_wrappers[observer_key] = ObserverThreadWrapper(
                    observer=observer_reference, observer_self=self_for_observer, logger=self.logger)
                self._connection_closed_handlers[observer_key] = connection_closed_handler

    def unsubscribe(self, observer, connection_closed_handler):
        """
        Unsubscribe from 'data-received notification'
        :param observer: function that was previously subscribed
        :param connection_closed_handler: callable to be called when connection is closed.
        """
        with self._observers_lock:
            self._log(level=TRACE, msg="unsubscribe({})".format(observer))
            observer_key, _ = self._get_observer_key_value(observer)
            if observer_key in self._observer_wrappers and observer_key in self._connection_closed_handlers:
                self._observer_wrappers[observer_key].request_stop()
                del self._connection_closed_handlers[observer_key]
                del self._observer_wrappers[observer_key]
            else:
                self._log(level=logging.WARNING,
                          msg="{} and {} were not both subscribed.".format(observer, connection_closed_handler),
                          levels_to_go_up=2)

    def shutdown(self):
        """
        Closes connection with notifying all observers about closing.
        :return: None
        """

        for handler in list(self._connection_closed_handlers.values()):
            handler()
        super(ThreadedMolerConnection, self).shutdown()

    def notify_observers(self, data, recv_time):
        """
        Notify all subscribed observers about data received on connection.
        :param data: data to send to all registered subscribers.
        :param recv_time: time of data really read form connection.
        :return None
        """
        subscribers_wrappers = list(self._observer_wrappers.values())
        for wrapper in subscribers_wrappers:
            wrapper.feed(data=data, recv_time=recv_time)

    def _check_observers_loop(self):
        for connection_observer in self._observers_runner:
            self._feed_connection_observer(connection_observer=connection_observer, stop_feeding=None, observer_lock=None)
            if connection_observer.done():
                self._to_remove_connection_observers.append(connection_observer)
        if self._to_remove_connection_observers:
            for connection_observer in self._to_remove_connection_observers:
                self._observers_runner.remove(connection_observer)
            self._to_remove_connection_observers.clear()

    def _feed_connection_observer(self, connection_observer, stop_feeding, observer_lock):
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


class RunnerForThreadedMolerConnection(ConnectionObserverRunner):

    def __init__(self):
        self._connections_obsevers = list()
        self._enable_loop_run_runner = True  # Set False to break loop.
        self._tick = 0.001

    def shutdown(self):
        """
        Cleanup used resources.
        :return: None
        """
        observers = self._connections_obsevers
        self._connections_obsevers = list()
        self._enable_loop_run_runner = False
        for connection_observer in observers:
            connection_observer.cancel()

    def submit(self, connection_observer):
        """
        Submit connection observer to background execution.
        Returns Future that could be used to await for connection_observer done.
        """
        assert connection_observer.life_status.start_time > 0.0  # connection-observer lifetime should already been
        self.add_connection_observer(connection_observer=connection_observer)

    def wait_for(self, connection_observer, connection_observer_future, timeout=10.0):
        """
        Await for connection_observer running in background or timeout.
        :param connection_observer: The one we are awaiting for.
        :param connection_observer_future: Future of connection-observer returned from submit(). Not used in this
        implementation.
        :param timeout: Max time (in float seconds) you want to await before you give up.
        :return:
        """
        if connection_observer.done():
            self.logger.debug("go foreground: {} is already done".format(connection_observer))
        else:
            max_timeout = timeout
            observer_timeout = connection_observer.timeout
            # we count timeout from now if timeout is given; else we use .life.status.start_time and .timeout of
            # observer
            start_time = time.time() if max_timeout else connection_observer.life_status.start_time
            await_timeout = max_timeout if max_timeout else observer_timeout
            if max_timeout:
                remain_time, msg = his_remaining_time("await max.", timeout=max_timeout, from_start_time=start_time)
            else:
                remain_time, msg = his_remaining_time("remaining", timeout=observer_timeout, from_start_time=start_time)
            self.logger.debug("go foreground: {} - {}".format(connection_observer, msg))

            # if connection_observer_future is None:
            #     end_of_life, remain_time = await_future_or_eol(connection_observer, remain_time, start_time, await_timeout,
            #                                                    self.logger)
            #     if end_of_life:
            #         return None
            if not self._execute_till_eol(connection_observer=connection_observer,
                                          #connection_observer_future=connection_observer_future,
                                          max_timeout=max_timeout,
                                          await_timeout=await_timeout,
                                          remain_time=remain_time):
                # code below is to close ConnectionObserver and future objects
                self._end_of_life_of_future_and_connection_observer(connection_observer=connection_observer)
        return None

    def _execute_till_eol(self, connection_observer, max_timeout, await_timeout, remain_time):
        eol_remain_time = remain_time
        # either we wait forced-max-timeout or we check done-status each 0.1sec tick
        if eol_remain_time > 0.0:
            # future = connection_observer_future or connection_observer._future
            # assert future is not None
            if max_timeout:
                if connection_observer.done():
                    return True
                # done, not_done = wait([future], timeout=remain_time)
                # if (future in done) or connection_observer.done():
                #     self._cancel_submitted_future(connection_observer, future)
                #     return True
                self._wait_for_time_out(connection_observer, timeout=await_timeout)
                if connection_observer.life_status.terminating_timeout > 0.0:
                    connection_observer.life_status.in_terminating = True
                    #done, not_done = wait([future], timeout=connection_observer.life_status.terminating_timeout)
                    #if (future in done) or connection_observer.done():
                    #    self._cancel_submitted_future(connection_observer, future)
                    return True
            else:
                while eol_remain_time > 0.0:
                    if connection_observer.done():
                        return True
                    already_passed = time.time() - connection_observer.life_status.start_time
                    eol_timeout = connection_observer.timeout + connection_observer.life_status.terminating_timeout
                    eol_remain_time = eol_timeout - already_passed
                    timeout = connection_observer.timeout
                    remain_time = timeout - already_passed
                    if remain_time <= 0.0:
                        self._wait_for_time_out(connection_observer=connection_observer, timeout=await_timeout)
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

    def wait_for_iterator(self, connection_observer, connection_observer_future):
        """
        Version of wait_for() intended to be used by Python3 to implement iterable/awaitable object.
        Note: we don't have timeout parameter here. If you want to await with timeout please do use timeout machinery
        of selected parallelism.
        :param connection_observer: The one we are awaiting for.
        :param connection_observer_future: Future of connection-observer returned from submit().
        :return: iterator
        """
        return None

    def feed(self, connection_observer):
        """
        Feeds connection_observer with data to let it become done.
        This is a place where runner is a glue between words of connection and connection-observer.
        Should be called from background-processing of connection observer.
        """
        pass  # For backward compatibility only

    def timeout_change(self, timedelta):
        """
        Call this method to notify runner that timeout has been changed in observer
        :param timedelta: delta timeout in float seconds
        :return: None
        """
        pass  # For backward compatibility only.

    def add_connection_observer(self, connection_observer):
        if connection_observer not in self._connections_obsevers:
            self._connections_obsevers.append(connection_observer)
            self._start_command(connection_observer=connection_observer)

    def _loop_for_runner(self):
        while self._enable_loop_run_runner:
            if not self._connections_obsevers:
                time.sleep(self._tick_for_runner)
            self._feed_connection_observers()
            self._check_last_feed_connection_observers()
            self._check_timeout_connection_observers()
            for connection_observer in self._connections_obsevers:
                try:
                    pass
                except Exception as ex:
                    self.logger.exception(msg=r'Exception from "{}" when running checking: "{}" "{!r}".'.format(
                        connection_observer, ex, repr(ex)
                    ))
            self._remove_unnecessary_connection_observers()

    def _check_last_feed_connection_observers(self):
        """
        Call on_inactivity on connection_observer if needed.
        :return: None
        """
        current_time = time.time()
        for connection_observer in self._connections_obsevers:
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
        for connection_observer in self._connections_obsevers:
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
                    self._time_out_observer(connection_observer=connection_observer,
                                            timeout=connection_observer.timeout, passed_time=run_duration,
                                            runner_logger=self.logger)
                    if connection_observer.life_status.terminating_timeout >= 0.0:
                        connection_observer.life_status.start_time = time.time()
                        connection_observer.life_status.in_terminating = True

    def _wait_for_time_out(self, connection_observer, timeout):
        passed = time.time() - connection_observer.life_status.start_time
        self.time_out_observer(connection_observer=connection_observer,
                               timeout=timeout, passed_time=passed,
                               runner_logger=self.logger, kind="await_done")

    def _timeout_observer(self, connection_observer, timeout, passed_time, runner_logger, kind="background_run"):
        """Set connection_observer status to timed-out"""
        if not connection_observer.life_status.was_on_timeout_called:
            connection_observer.life_status.was_on_timeout_called = True
            if not connection_observer.done():
                if connection_observer.is_command():
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

    def _remove_unnecessary_connection_observers(self):
        for connection_observer in self._connections_obsevers:
            if connection_observer.done():
                self._to_remove_connection_observers.append(connection_observer)
        if self._to_remove_connection_observers:
            for connection_observer in self._to_remove_connection_observers:
                self._connections_obsevers.remove(connection_observer)
            self._to_remove_connection_observers.clear()

    def _feed_connection_observers(self):
        try:
            data, timestamp = self._queue_for_connection_observers.get(True, self._tick_for_runner)
            feed_time = time.time()
            for connection_observer in self._connections_obsevers:
                try:
                    self.logger.log(level=TRACE, msg=r'notifying {}({!r})'.format(connection_observer, repr(data)))
                    connection_observer.data_received(data=data, recv_time=timestamp)
                except Exception as ex:
                    self.logger.exception(msg=r'Exception "{}" ("{}") inside: {} when processing ({!r})'.format(
                        ex, repr(ex), connection_observer, repr(data)))
                    connection_observer.set_exception(exception=ex)
                finally:
                    connection_observer.life_status.last_feed_time = feed_time
        except queue.Empty:
            pass  # No incoming data within self._tick_for_runner

    def _start_command(self, connection_observer):
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
