# -*- coding: utf-8 -*-
"""
Testing connection observer runner based on threads

- submit
- wait_for
"""
import pytest
import time
import threading

from moler.connection_observer import ConnectionObserver

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'


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
    connection_observer, awaited_data = observer_and_awaited_data
    connection_observer_future = observer_runner.submit(connection_observer)

    def inject_data():
        time.sleep(0.5)
        moler_conn = connection_observer.connection
        moler_conn.data_received(awaited_data)

    try:
        ext_io = threading.Thread(target=inject_data)
        ext_io.start()
        result = observer_runner.wait_for(connection_observer,
                                          connection_observer_future,
                                          timeout=1.0)
        assert not connection_observer_future.running()
        assert connection_observer_future.done()
        assert connection_observer.done()
        assert result == connection_observer_future.result()
    finally:  # test cleanup
        ext_io.join()
        connection_observer_future.cancel()


def test_can_await_connection_observer_to_timeout(connection_observer,
                                                  observer_runner):
    from moler.exceptions import ConnectionObserverTimeout

    connection_observer_future = observer_runner.submit(connection_observer)
    try:
        with pytest.raises(ConnectionObserverTimeout):
            observer_runner.wait_for(connection_observer,
                                     connection_observer_future,
                                     timeout=0.5)
        assert not connection_observer_future.running()
        assert connection_observer_future.done()
        assert connection_observer.done()
    finally:  # test cleanup
        connection_observer_future.cancel()


# TODO: tests for error cases


# --------------------------- resources ---------------------------


@pytest.yield_fixture()
def observer_runner():
    from moler.runner import ThreadPoolExecutorRunner
    runner = ThreadPoolExecutorRunner()
    yield runner
    runner.shutdown()


class NetworkDownDetector(ConnectionObserver):
    def __init__(self, connection=None):
        super(NetworkDownDetector, self).__init__(connection=connection)

    def data_received(self, data):
        """
        Awaiting change like:
        64 bytes from 10.0.2.15: icmp_req=3 ttl=64 time=0.045 ms
        ping: sendmsg: Network is unreachable
        """
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
