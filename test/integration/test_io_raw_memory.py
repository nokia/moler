# -*- coding: utf-8 -*-
"""
Testing external-IO FIFO-mem-buffer connection

- open/close (for threaded)
- send/receive (naming may differ)
"""
import pytest
import time

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'


# TODO: test open/close for threaded FIFO


def test_can_send_and_receive_data_from_connection(memory_connection):
    connection = memory_connection
    with connection:
        connection.write(b"command to be echoed")
        received_data = connection.read()
        assert b'command to be echoed' == received_data

        connection.inject(b"async msg")
        received_data = connection.read()
        assert b'async msg' == received_data


def test_will_not_receive_data_from_connection_when_echo_is_off(memory_connection):
    connection = memory_connection
    connection.echo = False
    with connection:
        connection.write(b"command to be echoed")
        received_data = connection.read()
        assert b'' == received_data


def test_can_receive_data_from_ext_io_into_moler_connection(memory_connection):
    connection = memory_connection
    received_data = {'data': ''}

    def receiver(data):
        received_data['data'] = data

    connection.moler_connection.subscribe(receiver)
    with connection:
        connection.write(b"command to be echoed")
        connection.read()
        assert 'command to be echoed' == received_data['data']

        connection.inject(b"async msg")
        connection.read()
        assert 'async msg' == received_data['data']


def test_can_send_data_into_ext_io_from_moler_connection(memory_connection):
    connection = memory_connection
    moler_conn = connection.moler_connection
    with connection:
        moler_conn.send("command to be echoed")
        received_data = connection.read()
        assert b'command to be echoed' == received_data


# TODO: tests for error cases raising Exceptions - if any?
# --------------------------- resources ---------------------------


@pytest.fixture()
def memory_connection():
    from moler.io.raw.memory import FifoBuffer
    from moler.connection import ObservableConnection
    moler_conn = ObservableConnection(decoder=lambda data: data.decode("utf-8"),
                                      encoder=lambda data: data.encode("utf-8"))
    return FifoBuffer(moler_connection=moler_conn)
