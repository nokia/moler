# -*- coding: utf-8 -*-
"""
Testing connection observer with external-IO

- call as function (synchronous)
- call as future  (asynchronous)
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import time

import pytest
from moler.connection_observer import ConnectionObserver


def test_calling_connection_observer_as_function(ping_lines_as_bytes,
                                                 ext_io_connection):
    """Connection observer should behave like function for synchronous call"""
    ext_io_remote_side = ext_io_connection
    moler_conn = ext_io_connection.moler_connection
    # we use it as function so we want verb:
    detect_network_down = NetworkDownDetector(connection=moler_conn)

    ext_io_remote_side.inject(input_bytes=ping_lines_as_bytes, delay=0.2)
    with ext_io_connection.open():
        # ------------------------------------------------+
        result = detect_network_down()  # <-- as function |
        # ------------------------------------------------+
        assert detect_network_down.done()
        assert result == detect_network_down.result()


def test_connection_observer_behaves_like_future(ping_lines_as_bytes,
                                                 ext_io_connection):
    """For async call"""
    ext_io_remote_side = ext_io_connection
    moler_conn = ext_io_connection.moler_connection
    # we use it as future so we want noun:
    network_down_detector = NetworkDownDetector(connection=moler_conn)

    ext_io_remote_side.inject(input_bytes=ping_lines_as_bytes, delay=0.2)
    with ext_io_connection.open():
        # ---------------------------------------------------------------------+
        future = network_down_detector.start()                  # <- as future |
        assert not future.done()                                # <- as future |
        assert not future.cancelled()                           # <- as future |
        assert future == network_down_detector                  # .            |
        # give concurrency-of-future a chance to gain control   # .            |
        time.sleep(0.1)                                         # .            |
        assert future.running()                                 # <- as future |
        result = network_down_detector.await_done(timeout=2.0)  # <- as future |
        assert result == network_down_detector.result()         # <- as future |
        # ---------------------------------------------------------------------+


# TODO: tests of futures: cancel(), failing observer, timeouting observer
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


@pytest.yield_fixture(params=['FIFO-in-memory'])
def ext_io_connection(request):
    from moler.io.raw.memory import ThreadedFifoBuffer
    from moler.threaded_moler_connection import ThreadedMolerConnection
    moler_conn = ThreadedMolerConnection(decoder=lambda data: data.decode("utf-8"))
    connection = ThreadedFifoBuffer(moler_connection=moler_conn)
    return connection


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
def ping_lines_as_bytes():
    ping_lines = [line.encode("utf-8") for line in ping_output.splitlines(True)]
    return ping_lines
