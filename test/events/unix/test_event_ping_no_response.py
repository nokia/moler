# -*- coding: utf-8 -*-

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'marcin.usielski@nokia.com'


import time
from moler.events.unix.ping_no_response import PingNoResponse
from moler.util.moler_test import MolerTest


def test_event_ping_no_response(buffer_connection):
    counter = dict()
    counter['nr'] = 0

    def callback_fun(param):
        param['nr'] += 1

    output = "From 192.168.255.126 icmp_seq=1 Destination Host Unreachable"
    event = PingNoResponse(connection=buffer_connection.moler_connection, till_occurs_times=2)
    event.add_event_occurred_callback(callback=callback_fun, callback_params={'param': counter})
    assert 0 == counter['nr']
    event.start()
    buffer_connection.moler_connection.data_received(output.encode("utf-8"), datetime.datetime.now())
    MolerTest.sleep(0.2)
    assert 1 == counter['nr']
    event.pause()
    buffer_connection.moler_connection.data_received(output.encode("utf-8"), datetime.datetime.now())
    MolerTest.sleep(0.2)
    assert 1 == counter['nr']
    event.resume()
    buffer_connection.moler_connection.data_received(output.encode("utf-8"), datetime.datetime.now())
    event.await_done()
    assert 2 == counter['nr']
    assert event.done() is True


def test_erase_not_full_line_on_pause(buffer_connection):
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
    run = True

    def feed_in_separate_thread():
        while run:
            buffer_connection.moler_connection.data_received("abcde\nfghi\njkl".encode("utf-8"), datetime.datetime.now())
            MolerTest.sleep(sleep_time/10)
    from threading import Thread
    tf = Thread(target=feed_in_separate_thread)
    tf.setDaemon(True)
    tf.start()
    start_time = time.time()

    while time.time() - start_time < 4 or processed['process'] < 300:
        event.pause()
        MolerTest.sleep(sleep_time)
        event.resume()
        MolerTest.sleep(sleep_time)
    event.resume()
    run = False
    MolerTest.sleep(0.2)
    buffer_connection.moler_connection.data_received(output.encode("utf-8"), datetime.datetime.now())
    buffer_connection.moler_connection.data_received(output.encode("utf-8"), datetime.datetime.now())
    event.await_done(timeout=1)
    assert event.done() is True
