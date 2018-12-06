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
import mock

import pytest
from moler.connection_observer import ConnectionObserver


@pytest.mark.asyncio
async def test_observer_gets_all_data_of_connection_after_it_is_submitted_to_background(observer_runner):
    # Raw 'def' usage note:
    # This functionality works as well when runner is used inside raw def function
    # since it only uses runner.submit() + awaiting time
    # another words - runner is running over some time period
    # The only difference is that raw def function may use only standalone_runner (which is subset of observer_runner)
    # and inside test you exchange 'await asyncio.sleep()' with 'time.sleep()'
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


@pytest.mark.asyncio
async def test_runner_unsubscribes_from_connection_after_runner_shutdown(observer_runner):
    # see - Raw 'def' usage note
    from moler.connection import ObservableConnection

    moler_conn = ObservableConnection()
    # check if shutdown unsubscribes all observers running inside given runner
    net_down_detector1 = NetworkDownDetector(connection=moler_conn)
    net_down_detector2 = NetworkDownDetector(connection=moler_conn)
    assert len(moler_conn._observers) == 0
    observer_runner.submit(net_down_detector1)
    observer_runner.submit(net_down_detector2)
    assert len(moler_conn._observers) == 2

    observer_runner.shutdown()
    await asyncio.sleep(0.1)
    assert len(moler_conn._observers) == 0


@pytest.mark.asyncio
async def test_runner_doesnt_break_on_exception_raised_inside_observer(observer_runner):
    """Runner should be secured against 'wrongly written' connection-observer"""
    # see - Raw 'def' usage note
    conn_observer = failing_net_down_detector(fail_on_data="zero bytes",
                                              fail_by_raising=Exception("unknown format"))
    connection = conn_observer.connection
    observer_runner.submit(conn_observer)

    connection.data_received("61 bytes")
    connection.data_received("zero bytes")
    connection.data_received("ping: Network is unreachable")

    assert conn_observer.all_data_received == ["61 bytes"]


@pytest.mark.asyncio
async def test_runner_sets_observer_exception_result_for_exception_raised_inside_observer(observer_runner):
    """Runner should correct behaviour of 'wrongly written' connection-observer"""
    # see - Raw 'def' usage note
    unknown_format_exception = Exception("unknown format")
    conn_observer = failing_net_down_detector(fail_on_data="zero bytes",
                                              fail_by_raising=unknown_format_exception)
    connection = conn_observer.connection
    observer_runner.submit(conn_observer)

    connection.data_received("61 bytes")
    connection.data_received("zero bytes")
    connection.data_received("ping: Network is unreachable")

    assert conn_observer._exception is unknown_format_exception


@pytest.mark.asyncio
async def test_future_is_not_exception_broken_when_observer_is_exception_broken(observer_runner):
    # see - Raw 'def' usage note
    conn_observer = failing_net_down_detector(fail_on_data="zero bytes",
                                              fail_by_raising=Exception("unknown format"))
    connection = conn_observer.connection
    future = observer_runner.submit(conn_observer)

    connection.data_received("61 bytes")
    connection.data_received("zero bytes")
    await asyncio.sleep(0.2)

    assert future.exception() is None


@pytest.mark.asyncio
async def test_future_doesnt_return_result_of_observer(observer_runner, net_down_detector):
    """Future just returns None when it is done"""
    # see - Raw 'def' usage note
    from moler.connection import ObservableConnection

    connection = net_down_detector.connection
    future = observer_runner.submit(net_down_detector)

    connection.data_received("61 bytes")
    connection.data_received("ping: Network is unreachable")
    await asyncio.sleep(0.2)

    assert future.result() is None


@pytest.mark.asyncio
async def test_future_timeouts_after_timeout_of_observer(observer_runner, connection_observer):
    """Observer has .timeout member"""
    # see - Raw 'def' usage note
    from moler.exceptions import ResultNotAvailableYet, MolerTimeout

    connection_observer.timeout = 0.1
    observer_runner.submit(connection_observer)
    with pytest.raises(ResultNotAvailableYet):
        connection_observer.result()
    await asyncio.sleep(0.2)
    with pytest.raises(MolerTimeout):
        connection_observer.result()


@pytest.mark.asyncio
async def test_future_accomodates_to_extending_timeout_of_observer(observer_runner, connection_observer):
    # see - Raw 'def' usage note
    from moler.exceptions import ResultNotAvailableYet, MolerTimeout

    connection_observer.timeout = 0.1
    observer_runner.submit(connection_observer)
    with pytest.raises(ResultNotAvailableYet):  # not timed out yet
        connection_observer.result()
    await asyncio.sleep(0.08)
    with pytest.raises(ResultNotAvailableYet):  # not timed out yet
        connection_observer.result()
    connection_observer.timeout = 0.15  # EXTEND
    await asyncio.sleep(0.05)
    with pytest.raises(ResultNotAvailableYet):  # not timed out yet
        connection_observer.result()
    await asyncio.sleep(0.04)
    with pytest.raises(MolerTimeout):  # should time out
        connection_observer.result()


@pytest.mark.asyncio
async def test_future_accomodates_to_shortening_timeout_of_observer(observer_runner, connection_observer):
    # see - Raw 'def' usage note
    from moler.exceptions import ResultNotAvailableYet, MolerTimeout

    connection_observer.timeout = 0.2
    observer_runner.submit(connection_observer)
    with pytest.raises(ResultNotAvailableYet):  # not timed out yet
        connection_observer.result()
    await asyncio.sleep(0.08)
    with pytest.raises(ResultNotAvailableYet):  # not timed out yet
        connection_observer.result()
    connection_observer.timeout = 0.1  # SHORTEN
    await asyncio.sleep(0.04)
    with pytest.raises(MolerTimeout):  # should time out
        connection_observer.result()


def test_wait_for__times_out_on_constructor_timeout(observer_runner, connection_observer):
    from moler.exceptions import MolerTimeout

    connection_observer.timeout = 0.2
    future = observer_runner.submit(connection_observer)
    start_time = time.time()
    with pytest.raises(MolerTimeout):
        observer_runner.wait_for(connection_observer, future,
                                 timeout=None)  # means: use .timeout of observer
        connection_observer.result()  # should raise Timeout
    duration = time.time() - start_time
    assert duration >= 0.2
    assert duration < 0.25


def test_wait_for__times_out_on_specified_timeout(observer_runner, connection_observer):
    from moler.exceptions import MolerTimeout

    connection_observer.timeout = 0.4
    future = observer_runner.submit(connection_observer)
    start_time = time.time()
    with pytest.raises(MolerTimeout):
        observer_runner.wait_for(connection_observer, future,
                                 timeout=0.2)  # means: use timeout of wait_for (shorter then initial one)
        connection_observer.result()  # should raise Timeout
    duration = time.time() - start_time
    assert duration >= 0.2
    assert duration < 0.25


def test_wait_for__times_out_on_earlier_timeout(observer_runner, connection_observer):
    from moler.exceptions import MolerTimeout

    connection_observer.timeout = 0.3
    future = observer_runner.submit(connection_observer)
    start_time = time.time()
    with pytest.raises(MolerTimeout):
        observer_runner.wait_for(connection_observer, future,
                                 timeout=0.5)  # means: timeout of wait_for longer then initial one
        connection_observer.result()  # should raise Timeout
    duration = time.time() - start_time
    assert duration >= 0.3
    assert duration < 0.35


def test_wait_for__tracks_changes_of_observer_timeout__extension(observer_runner, connection_observer):
    from moler.exceptions import MolerTimeout

    connection_observer.timeout = 0.2
    future = observer_runner.submit(connection_observer)
    start_time = time.time()

    def modify_observer_timeout():
        time.sleep(0.15)
        connection_observer.timeout = 0.35  # extend while inside wait_for()
    threading.Thread(target=modify_observer_timeout).start()

    with pytest.raises(MolerTimeout):
        observer_runner.wait_for(connection_observer, future,
                                 timeout=None)
        connection_observer.result()  # should raise Timeout
    duration = time.time() - start_time
    assert duration >= 0.35
    assert duration < 0.4


def test_wait_for__tracks_changes_of_observer_timeout__shortening(observer_runner, connection_observer):
    from moler.exceptions import MolerTimeout

    connection_observer.timeout = 0.35
    future = observer_runner.submit(connection_observer)
    start_time = time.time()

    def modify_observer_timeout():
        time.sleep(0.05)
        connection_observer.timeout = 0.2  # shorten while inside wait_for()
    threading.Thread(target=modify_observer_timeout).start()

    with pytest.raises(MolerTimeout):
        observer_runner.wait_for(connection_observer, future,
                                 timeout=None)
        connection_observer.result()  # should raise Timeout
    duration = time.time() - start_time
    assert duration >= 0.2
    assert duration < 0.25


def test_wait_for__direct_timeout_takes_precedence_over_extended_observer_timeout(observer_runner,
                                                                                  connection_observer):
    from moler.exceptions import MolerTimeout

    connection_observer.timeout = 0.2
    future = observer_runner.submit(connection_observer)
    start_time = time.time()

    def modify_observer_timeout():
        time.sleep(0.15)
        connection_observer.timeout = 0.35  # extend while inside wait_for()
    threading.Thread(target=modify_observer_timeout).start()

    with pytest.raises(MolerTimeout):
        observer_runner.wait_for(connection_observer, future,
                                 timeout=0.25)  # should take precedence, means: 0.25 sec from now
        connection_observer.result()  # should raise Timeout
    duration = time.time() - start_time
    assert duration >= 0.25
    assert duration < 0.3


@pytest.mark.asyncio
async def test_wait_for__is_prohibited_inside_async_def(async_runner, connection_observer):
    # can't raise in generic runner since why non-async-runner should bother about being used inside 'async def'
    # using them in such case is end-user error the same way as using time.sleep(2.41) inside 'async def'
    from moler.exceptions import WrongUsage

    # TODO: can we confidently check "called from async def"
    # https://stackoverflow.com/questions/30155138/how-can-i-write-asyncio-coroutines-that-optionally-act-as-regular-functions
    # "magically_determine_if_being_yielded_from() is actually event_loop.is_running()"
    # but that works for asyncio and not for curio/trio
    #
    # maybe we should just WARN - wait_for() is blocking, you should not use it inside 'async def'
    # as right now any user may use time.sleep(12) inside 'async def'
    # Any way to treat wait_for() as awaitable?
    #
    # If asyncio detects "slow/blocking" callback it logs it (asyncio/base_events.py def _run_once()):
    #     if dt >= self.slow_callback_duration:
    #         logger.warning('Executing %s took %.3f seconds',_format_handle(handle), dt)
    #
    # self.slow_callback_duration = 0.1 sec
    #
    # self._clock_resolution = 1e-09 = 0.000000001 s = 0.000001 ms = 0.001 us = 1ns (used by event loop scheduling)
    #
    # _run_once() realnie wola schedulowane funkcje. Wola je przez handle._run()
    # gdzie handle to TaskStepMethWrapper  ktory oddaje sterowanie do coroutyn
    # TaskStepMethWrapper to obiekt w C tworzony wewnatrz base_events.py def create_task()
    #     task = tasks.Task(coro, loop=self)  wola call_soon(TaskStepMethWrapper)
    #     opakowuje to jeszcze w events.Handle i opakowanego scheduluje: self._ready.append(handle)
    # wiec przypuszczenie ze ten wrapper wola .send() na generatorze/coroutynie i odbiera wynik z yielda
    future = async_runner.submit(connection_observer)
    with pytest.raises(WrongUsage) as err:
        # TODO: we should not allow 'wait_for()' inside 'async def' since it blocks asyncio-loop
        async_runner.wait_for(connection_observer, future)
        connection_observer.result()  # should raise WrongUsage
    print("\n")
    print(err.value)


def test_observer__on_timeout__is_called_once_at_timeout(observer_runner, connection_observer):
    from moler.exceptions import MolerTimeout

    connection_observer.timeout = 0.33
    future = observer_runner.submit(connection_observer)
    with mock.patch.object(connection_observer, "on_timeout") as timeout_callback:
        with pytest.raises(MolerTimeout):
            observer_runner.wait_for(connection_observer, future,
                                     timeout=0.33)  # means: timeout of wait_for longer then initial one
            connection_observer.result()  # should raise Timeout
        timeout_callback.assert_called_once()


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
def net_down_detector(connection_observer):  # let name say what type of observer it is
    return connection_observer


def failing_net_down_detector(fail_on_data, fail_by_raising):
    from moler.connection import ObservableConnection

    class FailingNetworkDownDetector(NetworkDownDetector):
        def data_received(self, data):
            if data == fail_on_data:
                raise fail_by_raising
            return super(FailingNetworkDownDetector, self).data_received(data)

    moler_conn = ObservableConnection()
    failing_detector = FailingNetworkDownDetector(connection=moler_conn)
    return failing_detector


@pytest.fixture()
def observer_and_awaited_data(connection_observer):
    awaited_data = 'ping: sendmsg: Network is unreachable'
    return connection_observer, awaited_data
