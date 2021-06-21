# -*- coding: utf-8 -*-
"""
Testing connection observer with runner based on threads

- call as function (synchronous)
- call as future  (asynchronous)
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import threading
import time

import pytest
from moler.connection_observer import ConnectionObserver
import datetime


def test_calling_connection_observer_returns_result(net_down_detector_and_ping_output):
    """Connection observer should behave like function for synchronous call"""
    connection_observer, ping_lines = net_down_detector_and_ping_output

    def inject_data():
        time.sleep(0.3)
        for line in ping_lines:
            time.sleep(0.1)
            moler_conn = connection_observer.connection
            moler_conn.data_received(line, datetime.datetime.now())

    ext_io = threading.Thread(target=inject_data)
    try:
        # we use it as function so we want verb:
        detect_network_down = connection_observer
        ext_io.start()
        result = detect_network_down()
        assert detect_network_down.done()
        assert result == detect_network_down.result()
    finally:  # test cleanup
        ext_io.join()


def test_connection_observer_behaves_like_future(net_down_detector_and_ping_output):
    """For async call"""
    connection_observer, ping_lines = net_down_detector_and_ping_output

    def inject_data():
        time.sleep(0.3)
        for line in ping_lines:
            time.sleep(0.1)
            moler_conn = connection_observer.connection
            moler_conn.data_received(line, datetime.datetime.now())

    ext_io = threading.Thread(target=inject_data)
    try:
        # we use it as future so we want noun:
        network_down_detector = connection_observer
        ext_io.start()
        future = network_down_detector.start()
        assert not future.done()
        assert not future.cancelled()
        assert future == network_down_detector
        time.sleep(0.1)  # give concurrency-of-future a chance to gain control
        assert future.running()
        result = network_down_detector.await_done(timeout=2.0)
        assert result == network_down_detector.result()
    finally:  # test cleanup
        ext_io.join()


# TODO: tests for error cases


# --------------------------- resources ---------------------------


class NetworkDownDetector(ConnectionObserver):
    def __init__(self, connection=None):
        super(NetworkDownDetector, self).__init__(connection=connection)

    def data_received(self, data, recv_time):
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
def net_down_detector():
    from moler.threaded_moler_connection import ThreadedMolerConnection
    moler_conn = ThreadedMolerConnection()
    observer = NetworkDownDetector(connection=moler_conn)
    return observer


ping_output = '''
greg@debian:~$ ping 10.0.2.15
PING 10.0.2.15 (10.0.2.15) 56(84) bytes of data.
64 bytes from 10.0.2.15: icmp_req=1 ttl=64 time=0.080 ms
64 bytes from 10.0.2.15: icmp_req=2 ttl=64 time=0.037 ms
64 bytes from 10.0.2.15: icmp_req=3 ttl=64 time=0.045 ms
ping: sendmsg: Network is unreachable
ping: sendmsg: Network is unreachable
ping: sendmsg: Network is unreachable
64 bytes from 10.0.2.15: icmp_req=7 ttl=64 time=0.123 ms
64 bytes from 10.0.2.15: icmp_req=8 ttl=64 time=0.056 ms
'''


@pytest.fixture()
def net_down_detector_and_ping_output(net_down_detector):
    ping_lines = ping_output.splitlines(True)
    return net_down_detector, ping_lines
