# -*- coding: utf-8 -*-
"""
Testing connection observer runner based on threads

- submit
- wait_for
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import threading
import time

import pytest
from moler.connection_observer import ConnectionObserver


def test_can_submit_connection_observer_into_background(connection_observer,
                                                        observer_runner):
    connection_observer_future = observer_runner.submit(connection_observer)
    # see API of concurrent.futures.Future
    try:
        assert not connection_observer_future.done()
        assert not connection_observer.done()
        time.sleep(0.1)  # give thread a chance to gain control
        assert connection_observer_future.running()
    finally:  # test cleanup
        connection_observer_future.cancel()


def test_can_await_connection_observer_to_complete(observer_and_awaited_data,
                                                   observer_runner):
    conn_observer, awaited_data = observer_and_awaited_data
    connection_observer_future = observer_runner.submit(conn_observer)

    def inject_data():
        time.sleep(0.5)
        moler_conn = conn_observer.connection
        moler_conn.data_received(awaited_data)

    ext_io = threading.Thread(target=inject_data)
    try:
        ext_io.start()
        observer_runner.wait_for(conn_observer,
                                          connection_observer_future,
                                          timeout=1.0)
        assert not connection_observer_future.running()
        assert connection_observer_future.done()
        assert conn_observer.done()
        assert connection_observer_future.result() is not None
    finally:  # test cleanup
        ext_io.join()
        connection_observer_future.cancel()


def test_CancellableFuture_can_be_cancelled_while_it_is_running(observer_runner):
    from concurrent.futures import ThreadPoolExecutor, CancelledError
    from moler.runner import CancellableFuture
    # concurrent.futures.Future can't cancel() while it is already running

    is_started = threading.Event()
    stop_running = threading.Event()
    is_done = threading.Event()

    def activity(is_started, stop_running, is_done):
        is_started.set()
        while not stop_running.is_set():
            time.sleep(0.1)
        is_done.set()

    future = ThreadPoolExecutor().submit(activity, is_started, stop_running, is_done)
    c_future = CancellableFuture(future, is_started, stop_running, is_done)
    try:
        is_started.wait(timeout=0.5)
        assert is_started.is_set()
        cancelled = c_future.cancel()
        time.sleep(0.1)  # allow threads switch
        assert is_done.is_set()
        assert cancelled is True
        assert c_future.cancelled()
        assert c_future.done()
        with pytest.raises(CancelledError):
            c_future.result()
    except AssertionError:
        raise
    finally:
        stop_running.set()

def test_can_await_connection_observer_to_timeout(connection_observer,
                                                  observer_runner):
    from moler.exceptions import ConnectionObserverTimeout

    connection_observer_future = observer_runner.submit(connection_observer)
    try:
        with pytest.raises(ConnectionObserverTimeout):
            observer_runner.wait_for(connection_observer,
                                     connection_observer_future,
                                     timeout=0.5)
            connection_observer.result()
        assert not connection_observer_future.running()
        assert connection_observer_future.done()
        assert connection_observer.done()
    finally:  # test cleanup
        connection_observer_future.cancel()


def test_connection_observer_with_unhandled_exception_is_made_done_with_exception_stored(observer_runner):
    from moler.connection import ObservableConnection

    fail_exc = Exception("Fail inside observer")
    class FailingObserver(ConnectionObserver):
        def data_received(self, data):
            raise fail_exc

    moler_conn = ObservableConnection()
    connection_observer = FailingObserver(connection=moler_conn)
    connection_observer_future = observer_runner.submit(connection_observer)
    assert connection_observer_future.running()
    try:
        moler_conn.data_received("data")  # will route to data_received() of observer

        assert connection_observer.done()
        assert connection_observer._exception is fail_exc
        time.sleep(0.1)  # let feeder exit on observer.done, let future realize this
        assert not connection_observer_future.running()
        assert connection_observer_future.done()
    finally:  # test cleanup
        connection_observer_future.cancel()


def test_gets_all_data_of_connection_after_it_is_started(observer_runner):
    from moler.connection import ObservableConnection

    for n in range(20):  # need to test multiple times because of thread races
        moler_conn = ObservableConnection()
        net_down_detector = NetworkDownDetector(connection=moler_conn, runner=observer_runner)
        connection = net_down_detector.connection
        net_down_detector.start()

        connection.data_received("61 bytes")
        connection.data_received("62 bytes")
        connection.data_received("ping: Network is unreachable")

        assert net_down_detector.all_data_received == ["61 bytes", "62 bytes", "ping: Network is unreachable"]


# TODO: tests for error cases


# --------------------------- resources ---------------------------


@pytest.yield_fixture()
def observer_runner():
    from moler.runner import ThreadPoolExecutorRunner
    runner = ThreadPoolExecutorRunner()
    yield runner
    runner.shutdown()


class NetworkDownDetector(ConnectionObserver):
    def __init__(self, connection=None, runner=None):
        super(NetworkDownDetector, self).__init__(connection=connection, runner=runner)
        self.all_data_received = []

    def data_received(self, data):
        """
        Awaiting change like:
        64 bytes from 10.0.2.15: icmp_req=3 ttl=64 time=0.045 ms
        ping: sendmsg: Network is unreachable
        """
        self.all_data_received.append(data)
        if not self.done():
            if "Network is unreachable" in data:
                when_detected = time.time()
                self.set_result(result=when_detected)


@pytest.fixture()
def connection_observer():
    from moler.connection import ObservableConnection
    moler_conn = ObservableConnection()
    observer = NetworkDownDetector(connection=moler_conn)
    return observer


@pytest.fixture()
def observer_and_awaited_data(connection_observer):
    awaited_data = 'ping: sendmsg: Network is unreachable'
    return connection_observer, awaited_data
