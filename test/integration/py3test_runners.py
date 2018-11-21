# -*- coding: utf-8 -*-
"""
Testing connection observer runner API that should be fullfilled by any runner

- submit
- wait_for
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import sys
import threading
import time
import platform
import importlib
import asyncio

import pytest
from moler.connection_observer import ConnectionObserver


def test_observer_gets_all_data_of_connection_after_it_is_submitted_to_background(observer_runner):
    from moler.connection import ObservableConnection

    for n in range(20):  # need to test multiple times because of thread races
        moler_conn = ObservableConnection()
        net_down_detector = NetworkDownDetector(connection=moler_conn)
        connection = net_down_detector.connection
        observer_runner.submit(net_down_detector)

        connection.data_received("61 bytes")
        connection.data_received("62 bytes")
        connection.data_received("ping: Network is unreachable")

        assert net_down_detector.all_data_received == ["61 bytes", "62 bytes", "ping: Network is unreachable"]


@pytest.mark.asyncio
async def test_observer_gets_all_data_after_async_runner_submit_from_running_loop(event_loop, async_runner):
    from moler.connection import ObservableConnection

    for n in range(1):  # need to test multiple times because of thread races
        moler_conn = ObservableConnection()
        net_down_detector = NetworkDownDetector(connection=moler_conn)
        connection = net_down_detector.connection
        async_runner.submit(net_down_detector)

        connection.data_received("61 bytes")
        connection.data_received("62 bytes")
        connection.data_received("ping: Network is unreachable")

        assert net_down_detector.all_data_received == ["61 bytes", "62 bytes", "ping: Network is unreachable"]


@pytest.mark.asyncio
async def test_runner_doesnt_break_on_exception_raised_inside_observer(event_loop, async_runner):
    """Runner should be secured against 'wrongly written' connection-observer"""
    from moler.connection import ObservableConnection

    class FailingNetworkDownDetector(NetworkDownDetector):
        def data_received(self, data):
            if data == "zero bytes":
                raise Exception("unknown format")
            return super(FailingNetworkDownDetector, self).data_received(data)

    moler_conn = ObservableConnection()
    net_down_detector = FailingNetworkDownDetector(connection=moler_conn)
    connection = net_down_detector.connection
    async_runner.submit(net_down_detector)

    connection.data_received("61 bytes")
    connection.data_received("zero bytes")
    connection.data_received("ping: Network is unreachable")

    assert net_down_detector.all_data_received == ["61 bytes"]


@pytest.mark.asyncio
async def test_runner_sets_observer_exception_result_for_exception_raised_inside_observer(event_loop, async_runner):
    """Runner should correct behaviour of 'wrongly written' connection-observer"""
    from moler.connection import ObservableConnection

    unknown_format_exception = Exception("unknown format")

    class FailingNetworkDownDetector(NetworkDownDetector):
        def data_received(self, data):
            if data == "zero bytes":
                raise unknown_format_exception
            return super(FailingNetworkDownDetector, self).data_received(data)

    moler_conn = ObservableConnection()
    net_down_detector = FailingNetworkDownDetector(connection=moler_conn)
    connection = net_down_detector.connection
    async_runner.submit(net_down_detector)

    connection.data_received("61 bytes")
    connection.data_received("zero bytes")
    connection.data_received("ping: Network is unreachable")

    assert net_down_detector._exception is unknown_format_exception


# TODO: tests for error cases
# TODO: handling not awaited futures (infinite background observer, timeouting observer but "failing path stopped"

# --------------------------- resources ---------------------------

def is_python36_or_above():
    (ver_major, ver_minor, _) = platform.python_version().split('.')
    return (ver_major == '3') and (int(ver_minor) >= 6)


available_bg_runners = [] #['runner.ThreadPoolExecutorRunner']
available_async_runners = []
if is_python36_or_above():
    # available_bg_runners.append('asyncio_runner.AsyncioRunner')
    # available_async_runners.append('asyncio_runner.AsyncioRunner')
    available_bg_runners.append('asyncio_runner.AsyncioInThreadRunner')
    available_async_runners.append('asyncio_runner.AsyncioInThreadRunner')


@pytest.yield_fixture(params=available_bg_runners)
def observer_runner(request):
    module_name, class_name = request.param.rsplit('.', 1)
    module = importlib.import_module('moler.{}'.format(module_name))
    runner_class = getattr(module, class_name)
    runner = runner_class()
    # NOTE: AsyncioRunner given here will start without running event loop
    yield runner
    runner.shutdown()


@pytest.yield_fixture(params=available_async_runners)
def async_runner(request):
    module_name, class_name = request.param.rsplit('.', 1)
    module = importlib.import_module('moler.{}'.format(module_name))
    runner_class = getattr(module, class_name)
    runner = runner_class()
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
