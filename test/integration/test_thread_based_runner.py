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


def test_future_lifetime_starts_from_runner_submit(connection_observer,
                                                   observer_runner):
    before_submit_time = time.time()
    connection_observer_future = observer_runner.submit(connection_observer)
    assert hasattr(connection_observer_future, "start_time")
    assert connection_observer_future.start_time > before_submit_time

    # TODO: ask runner (knows type of his future)
    # observer_runner.remaining_lifetime(connection_observer_future)
    # or
    # connection_observer_future.remaining_lifetime()


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
    start_time = time.time()
    c_future = CancellableFuture(future, start_time, is_started, stop_running, is_done)
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
