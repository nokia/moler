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

    durations = []
    for n in range(20):  # need to test multiple times to ensure there are no thread races
        moler_conn = ObservableConnection()
        net_down_detector = NetworkDownDetector(connection=moler_conn)
        connection = net_down_detector.connection
        start_time = time.time()
        observer_runner.submit(net_down_detector)
        durations.append(time.time() - start_time)

        connection.data_received("61 bytes")
        connection.data_received("62 bytes")
        connection.data_received("ping: Network is unreachable")

        assert net_down_detector.all_data_received == ["61 bytes", "62 bytes", "ping: Network is unreachable"]
    print("\n{}.submit() duration == {}".format(observer_runner.__class__.__name__,
                                                float(sum(durations))/len(durations)))


def test_runner_secures_observer_against_additional_data_after_observer_is_done(observer_runner):
    """Done observer should not get data even before unsubscribe from moler-connection"""
    # correctly written observer looks like:
    #
    # def data_received(self, data):
    #     if not self.done():
    #         parse(data)
    #
    # This test checks if runners secure wrong-written-observers with missing 'if not self.done():'
    from moler.connection import ObservableConnection

    for n in range(20):  # need to test multiple times to ensure there are no thread races
        moler_conn = ObservableConnection()
        net_down_detector = NetworkDownDetector(connection=moler_conn)
        connection = net_down_detector.connection
        observer_runner.submit(net_down_detector)

        connection.data_received("61 bytes")
        connection.data_received("ping: Network is unreachable")
        connection.data_received("62 bytes")

        assert net_down_detector.all_data_received == ["61 bytes", "ping: Network is unreachable"]


def test_runner_secures_observer_against_additional_data_after_runner_shutdown(observer_runner):
    """In-shutdown runner should not pass data to observer even before unsubscribe from moler-connection"""
    # Even without running background feeder
    # we can use correctly constructed secure_data_received(data)
    # to block passing data from connection to observer while runner is in-shutdown state
    from moler.connection import ObservableConnection

    moler_conn = ObservableConnection()
    # check if shutdown stops all observers running inside given runner
    net_down_detector1 = NetworkDownDetector(connection=moler_conn)
    net_down_detector2 = NetworkDownDetector(connection=moler_conn)
    connection = moler_conn
    observer_runner.submit(net_down_detector1)
    observer_runner.submit(net_down_detector2)

    connection.data_received("61 bytes")
    observer_runner.shutdown()
    connection.data_received("62 bytes")

    assert net_down_detector1.all_data_received == ["61 bytes"]
    assert net_down_detector2.all_data_received == ["61 bytes"]


def test_runner_unsubscribes_from_connection_after_runner_shutdown(standalone_runner):
    from moler.connection import ObservableConnection

    moler_conn = ObservableConnection()
    # check if shutdown unsubscribes all observers running inside given runner
    net_down_detector1 = NetworkDownDetector(connection=moler_conn)
    net_down_detector2 = NetworkDownDetector(connection=moler_conn)
    connection = moler_conn
    assert len(moler_conn._observers) == 0
    standalone_runner.submit(net_down_detector1)
    standalone_runner.submit(net_down_detector2)
    assert len(moler_conn._observers) == 2

    standalone_runner.shutdown()
    time.sleep(0.1)
    assert len(moler_conn._observers) == 0


@pytest.mark.asyncio
async def test_runner_unsubscribes_from_connection_after_runner_shutdown_from_running_loop(observer_runner):
    from moler.connection import ObservableConnection

    moler_conn = ObservableConnection()
    # check if shutdown unsubscribes all observers running inside given runner
    net_down_detector1 = NetworkDownDetector(connection=moler_conn)
    net_down_detector2 = NetworkDownDetector(connection=moler_conn)
    connection = moler_conn
    assert len(moler_conn._observers) == 0
    observer_runner.submit(net_down_detector1)
    observer_runner.submit(net_down_detector2)
    assert len(moler_conn._observers) == 2

    observer_runner.shutdown()
    await asyncio.sleep(0.1)
    assert len(moler_conn._observers) == 0


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


def test_future_is_not_exception_broken_when_observer_is_exception_broken(standalone_runner):
    from moler.connection import ObservableConnection

    class FailingNetworkDownDetector(NetworkDownDetector):
        def data_received(self, data):
            if data == "zero bytes":
                raise Exception("unknown format")
            return super(FailingNetworkDownDetector, self).data_received(data)

    moler_conn = ObservableConnection()
    net_down_detector = FailingNetworkDownDetector(connection=moler_conn)
    connection = net_down_detector.connection
    future = standalone_runner.submit(net_down_detector)

    connection.data_received("61 bytes")
    connection.data_received("zero bytes")
    time.sleep(0.2)

    assert future.exception() is None


@pytest.mark.asyncio
async def test_asyncfuture_is_not_exception_broken_when_observer_is_exception_broken(event_loop, async_runner):
    from moler.connection import ObservableConnection

    class FailingNetworkDownDetector(NetworkDownDetector):
        def data_received(self, data):
            if data == "zero bytes":
                raise Exception("unknown format")
            return super(FailingNetworkDownDetector, self).data_received(data)

    moler_conn = ObservableConnection()
    net_down_detector = FailingNetworkDownDetector(connection=moler_conn)
    connection = net_down_detector.connection
    future = async_runner.submit(net_down_detector)

    connection.data_received("61 bytes")
    connection.data_received("zero bytes")
    await asyncio.sleep(0.2)

    assert future.exception() is None


def test_future_doesnt_return_result_of_observer(standalone_runner):
    """Future just returns None when it is done"""
    from moler.connection import ObservableConnection

    moler_conn = ObservableConnection()
    net_down_detector = NetworkDownDetector(connection=moler_conn)
    connection = net_down_detector.connection
    future = standalone_runner.submit(net_down_detector)

    connection.data_received("61 bytes")
    connection.data_received("ping: Network is unreachable")
    time.sleep(0.2)

    assert future.result() is None


@pytest.mark.asyncio
async def test_asyncfuture_doesnt_return_result_of_observer(event_loop, async_runner):
    """Future just returns None when it is done"""
    from moler.connection import ObservableConnection

    moler_conn = ObservableConnection()
    net_down_detector = NetworkDownDetector(connection=moler_conn)
    connection = net_down_detector.connection
    future = async_runner.submit(net_down_detector)

    connection.data_received("61 bytes")
    connection.data_received("ping: Network is unreachable")
    await asyncio.sleep(0.2)

    assert future.result() is None

# TODO: tests for error cases
# TODO: handling not awaited futures (infinite background observer, timeouting observer but "failing path stopped"

# --------------------------- resources ---------------------------

def is_python36_or_above():
    (ver_major, ver_minor, _) = platform.python_version().split('.')
    return (ver_major == '3') and (int(ver_minor) >= 6)


# bg_runners may be called from both 'async def' and raw 'def' functions
available_bg_runners = ['runner.ThreadPoolExecutorRunner']
# standalone_runners may run without giving up control to some event loop (since they create own thread(s))
available_standalone_runners = ['runner.ThreadPoolExecutorRunner']
# async_runners may be called only from 'async def' functions and require already running events-loop
available_async_runners = []
if is_python36_or_above():
    available_bg_runners.append('asyncio_runner.AsyncioRunner')
    available_async_runners.append('asyncio_runner.AsyncioRunner')
    available_bg_runners.append('asyncio_runner.AsyncioInThreadRunner')
    available_async_runners.append('asyncio_runner.AsyncioInThreadRunner')
    available_standalone_runners.append('asyncio_runner.AsyncioInThreadRunner')


@pytest.yield_fixture(params=available_bg_runners)
def observer_runner(request):
    module_name, class_name = request.param.rsplit('.', 1)
    module = importlib.import_module('moler.{}'.format(module_name))
    runner_class = getattr(module, class_name)
    runner = runner_class()
    # NOTE: AsyncioRunner given here will start without running event loop
    yield runner
    runner.shutdown()


@pytest.yield_fixture(params=available_standalone_runners)
def standalone_runner(request):
    module_name, class_name = request.param.rsplit('.', 1)
    module = importlib.import_module('moler.{}'.format(module_name))
    runner_class = getattr(module, class_name)
    runner = runner_class()
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
