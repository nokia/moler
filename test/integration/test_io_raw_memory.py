# -*- coding: utf-8 -*-
"""
Testing external-IO FIFO-mem-buffer connection

- open/close (for threaded)
- send/receive (naming may differ)
"""
import importlib
import time

import pytest

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'


# TODO: test open/close for threaded FIFO


def test_can_send_and_receive_data_from_connection(memory_connection_without_decoder):
    connection = memory_connection_without_decoder
    moler_conn = connection.moler_connection
    received_data = bytearray()

    def receiver(data):
        received_data.extend(data)

    moler_conn.subscribe(receiver)
    with connection:
        connection.write(b"command to be echoed")
        connection.read()
        assert b'command to be echoed' == received_data

        received_data = bytearray()  # cleanup
        connection.inject([b"async msg1\n", b"async msg2\n"])
        connection.read()
        assert b'async msg1\nasync msg2\n' == received_data


def test_will_not_receive_data_from_connection_when_echo_is_off(memory_connection_without_decoder):
    connection = memory_connection_without_decoder
    connection.echo = False
    moler_conn = connection.moler_connection
    received_data = bytearray()

    def receiver(data):
        received_data.extend(data)

    moler_conn.subscribe(receiver)
    with connection:
        connection.write(b"command to be echoed")
        connection.read()
        assert b'' == received_data


def test_can_inject_data_with_specified_delay(memory_connection_without_decoder):
    connection = memory_connection_without_decoder
    moler_conn = connection.moler_connection
    received_data = bytearray()
    start_time = time.time()

    def receiver(data):
        received_data.extend(data)
        if b"msg3" in received_data:
            duration = time.time() - start_time
            assert b'msg1\nmsg2\nmsg3\n' == received_data
            assert (duration > 0.7) and (duration < 0.8)

    moler_conn.subscribe(receiver)
    with connection:
        connection.inject(input_bytes=[b"msg1\n", b"msg2\n", b"msg3\n"],
                          delay=0.25)
        connection.read()


def test_inject_response_awaits_nearest_write_before_responding(memory_connection_without_decoder):
    connection = memory_connection_without_decoder
    moler_conn = connection.moler_connection
    received_data = bytearray()

    def receiver(data):
        received_data.extend(data)

    moler_conn.subscribe(receiver)
    with connection:
        connection.inject_response(input_bytes=[b'response\n'])
        connection.read()
        assert b'' == received_data  # injection not active yet
        connection.write(b'request\n')
        connection.read()
        assert b'request\nresponse\n' == received_data


def test_can_receive_data_from_ext_io_into_moler_connection(memory_connection):
    connection = memory_connection
    received_data = {'data': ''}  # expecting data decoded into str

    def receiver(data):
        received_data['data'] += data

    connection.moler_connection.subscribe(receiver)
    with connection:
        connection.write(b"command to be echoed")
        connection.read()
        assert 'command to be echoed' == received_data['data']

        received_data = {'data': ''}  # cleanup
        connection.inject(b"async msg")  # can also inject byte-by-byte
        connection.read()
        assert 'async msg' == received_data['data']


def test_can_send_data_into_ext_io_from_moler_connection(memory_connection_without_decoder):
    connection = memory_connection_without_decoder
    moler_conn = connection.moler_connection
    received_data = bytearray()

    def receiver(data):
        received_data.extend(data)

    moler_conn.subscribe(receiver)
    with connection:
        moler_conn.send("command to be echoed")
        connection.read()
        assert b'command to be echoed' == received_data


# TODO: tests for error cases raising Exceptions - if any?
# --------------------------- resources ---------------------------


@pytest.fixture(params=['FifoBuffer', 'ThreadedFifoBuffer'])
def memory_connection_class(request):
    class_name = request.param
    module = importlib.import_module('moler.io.raw.memory')
    connection_class = getattr(module, class_name)
    return connection_class


@pytest.fixture
def memory_connection(memory_connection_class):
    connection_class = memory_connection_class
    from moler.connection import ObservableConnection
    moler_conn = ObservableConnection(decoder=lambda data: data.decode("utf-8"),
                                      encoder=lambda data: data.encode("utf-8"))
    connection = connection_class(moler_connection=moler_conn)
    return connection


@pytest.fixture
def memory_connection_without_decoder(memory_connection_class):
    connection_class = memory_connection_class
    from moler.connection import ObservableConnection
    moler_conn = ObservableConnection(encoder=lambda data: data.encode("utf-8"))
    connection = connection_class(moler_connection=moler_conn)
    return connection
