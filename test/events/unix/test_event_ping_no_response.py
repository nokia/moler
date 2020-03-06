# -*- coding: utf-8 -*-

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'marcin.usielski@nokia.com'


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
    buffer_connection.moler_connection.data_received(output.encode("utf-8"))
    MolerTest.sleep(0.2)
    assert 1 == counter['nr']
    event.pause()
    buffer_connection.moler_connection.data_received(output.encode("utf-8"))
    MolerTest.sleep(0.2)
    assert 1 == counter['nr']
    event.resume()
    buffer_connection.moler_connection.data_received(output.encode("utf-8"))
    event.await_done()
    assert 2 == counter['nr']
    assert event.done() is True
