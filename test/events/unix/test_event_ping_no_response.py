# -*- coding: utf-8 -*-

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2020-2024, Nokia'
__email__ = 'marcin.usielski@nokia.com'


import time
import pytest
from moler.events.unix.ping_no_response import PingNoResponse
from moler.util.moler_test import MolerTest
from moler.exceptions import MolerException
import datetime


def test_event_ping_no_response(buffer_connection):
    counter = dict()
    counter['nr'] = 0
    sleep_time = 0.4
    max_timeout = 5.0

    def callback_fun(param):
        param['nr'] += 1

    output = "From 192.168.255.126 icmp_seq=1 Destination Host Unreachable"
    event = PingNoResponse(connection=buffer_connection.moler_connection, till_occurs_times=2)
    event.add_event_occurred_callback(callback=callback_fun, callback_params={'param': counter})
    assert 0 == counter['nr']
    event.start()
    buffer_connection.moler_connection.data_received(output.encode("utf-8"), datetime.datetime.now())
    start_time = time.monotonic()
    while time.monotonic() - start_time <= max_timeout:
        if 1 == counter['nr']:
            break
        MolerTest.sleep(sleep_time)
    assert 1 == counter['nr']
    event.pause()
    buffer_connection.moler_connection.data_received(output.encode("utf-8"), datetime.datetime.now())
    MolerTest.sleep(sleep_time)
    assert 1 == counter['nr']
    event.resume()
    buffer_connection.moler_connection.data_received(output.encode("utf-8"), datetime.datetime.now())
    event.await_done()
    start_time = time.monotonic()
    while time.monotonic() - start_time <= max_timeout:
        if 2 == counter['nr']:
            break
        MolerTest.sleep(sleep_time)
    assert 2 == counter['nr']
    assert event.done() is True


def test_erase_not_full_line_on_pause(buffer_connection):
    import threading
    output = "From 192.168.255.126 icmp_seq=1 Destination Host Unreachable"
    sleep_time = 0.0005
    processed = {'process': 0}

    class PingNoResponseDelay(PingNoResponse):
        def _process_line_from_output(self, current_chunk, line, is_full_line):
            processed['process'] += 1
            MolerTest.sleep(seconds=sleep_time)
            super(PingNoResponseDelay, self)._process_line_from_output(current_chunk=current_chunk,
                                                                       line=line, is_full_line=is_full_line)

    event = PingNoResponseDelay(connection=buffer_connection.moler_connection, till_occurs_times=2)
    event.start()
    stopped = threading.Event()

    def feed_in_separate_thread():
        cnt = 1
        while not stopped.is_set():
            data = f"[{cnt}] abcde\nfghi\njkl"
            buffer_connection.moler_connection.data_received(data.encode("utf-8"), datetime.datetime.now())
            MolerTest.sleep(sleep_time/10)
            cnt += 1
        MolerTest.info(f"feed_in_separate_thread() exited after producing {cnt} records")

    tf = threading.Thread(target=feed_in_separate_thread)
    tf.start()
    start_time = time.monotonic()

    while (time.monotonic() - start_time < 4) or (processed['process'] < 300):
        event.pause()
        MolerTest.sleep(sleep_time)
        event.resume()
        MolerTest.sleep(sleep_time)
    event.pause()  # force textual event to drop data from ObserverThreadWrapper queue being flushed
    stopped.set()
    tf.join()
    MolerTest.sleep(1)  # allow ObserverThreadWrapper to flush all data from queue
    MolerTest.info("Reactivating PingNoResponseDelay event")
    event.resume()
    buffer_connection.moler_connection.data_received(output.encode("utf-8"), datetime.datetime.now())
    buffer_connection.moler_connection.data_received(output.encode("utf-8"), datetime.datetime.now())
    event.await_done(timeout=1)
    assert event.done() is True


def test_break_event(buffer_connection):
    output = "From 192.168.255.126 icmp_seq=1 Destination Host Unreachable"
    event = PingNoResponse(connection=buffer_connection.moler_connection, till_occurs_times=-1)
    event.start()
    buffer_connection.moler_connection.data_received(output.encode("utf-8"), datetime.datetime.now())
    buffer_connection.moler_connection.data_received(output.encode("utf-8"), datetime.datetime.now())
    buffer_connection.moler_connection.data_received(output.encode("utf-8"), datetime.datetime.now())
    time.sleep(0.1)
    assert event.done() is False
    assert event.running() is True
    event.break_event()
    assert event.done() is True
    assert event.running() is False
    assert event.result() is not None
    result = event.result()
    assert len(result) == 3


def test_break_event_expected(buffer_connection):
    output = "From 192.168.255.126 icmp_seq=1 Destination Host Unreachable"
    event = PingNoResponse(connection=buffer_connection.moler_connection, till_occurs_times=3)
    event.start()
    buffer_connection.moler_connection.data_received(output.encode("utf-8"), datetime.datetime.now())
    buffer_connection.moler_connection.data_received(output.encode("utf-8"), datetime.datetime.now())
    time.sleep(0.1)
    event.break_event()
    with pytest.raises(MolerException) as exc:
        event.result()
    assert "Expected 3 occurrences but got 2" in str(exc.value)