# -*- coding: utf-8 -*-

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'marcin.usielski@nokia.com'


import time
from moler.events.unix.ping_no_response import PingNoResponse
from moler.util.moler_test import MolerTest
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
    start_time = time.time()
    while time.time() - start_time <= max_timeout:
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
    start_time = time.time()
    while time.time() - start_time <= max_timeout:
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
        while not stopped.isSet():
            data = "[{}] abcde\nfghi\njkl".format(cnt)
            buffer_connection.moler_connection.data_received(data.encode("utf-8"), datetime.datetime.now())
            MolerTest.sleep(sleep_time/10)
            cnt += 1
        MolerTest.info("feed_in_separate_thread() exited after producing {} records".format(cnt))

    tf = threading.Thread(target=feed_in_separate_thread)
    tf.start()
    start_time = time.time()

    while (time.time() - start_time < 4) or (processed['process'] < 300):
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
