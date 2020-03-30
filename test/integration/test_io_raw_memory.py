# -*- coding: utf-8 -*-
"""
Testing external-IO FIFO-mem-buffer connection

- open/close (for threaded)
- send/receive (naming may differ)
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018-2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import importlib
import time
from moler.util.moler_test import MolerTest

import pytest


# TODO: test open/close for threaded FIFO


def connection_closed_handler():
    pass


def test_can_assign_name_to_connection(memory_connection_class):
    from moler.connection import Connection

    moler_conn = Connection()
    connection = memory_connection_class(moler_connection=moler_conn,
                                         name="ctrl_server")
    assert connection.name == "ctrl_server"


def test_uses_moler_connection_name_if_none_given(memory_connection_class):
    from moler.connection import Connection

    moler_conn = Connection()
    connection = memory_connection_class(moler_connection=moler_conn)
    assert connection.name == moler_conn.name


def test_overwrites_moler_connection_name_with_own_one(memory_connection_class):
    from moler.connection import Connection

    moler_conn = Connection()
    # during construction
    connection = memory_connection_class(moler_connection=moler_conn, name="web_srv")
    assert moler_conn.name == "web_srv"
    # during direct attribute set
    connection.name = "http_srv"
    assert moler_conn.name == "http_srv"


def test_can_use_provided_logger(memory_connection_class):
    from moler.connection import Connection
    import logging

    moler_conn = Connection()
    connection = memory_connection_class(moler_connection=moler_conn,
                                         logger_name="conn.web_srv")
    assert isinstance(connection.logger, logging.Logger)
    assert connection.logger.name == "conn.web_srv"


def test_can_switch_off_logging(memory_connection_class):
    from moler.connection import Connection

    moler_conn = Connection()
    connection = memory_connection_class(moler_connection=moler_conn,
                                         logger_name=None)
    assert connection.logger is None


def test_can_use_default_logger_based_on_connection_name(memory_connection_class):
    from moler.connection import Connection
    import logging

    moler_conn = Connection()
    connection = memory_connection_class(moler_connection=moler_conn, name="ABC")
    assert isinstance(connection.logger, logging.Logger)
    assert connection.logger.name == "moler.connection.ABC.io"

    moler_conn = Connection()
    connection = memory_connection_class(moler_connection=moler_conn)
    assert isinstance(connection.logger, logging.Logger)
    assert connection.logger.name == "moler.connection.{}.io".format(connection.name)


def test_can_use_default_logger_based_on_moler_connection_name(memory_connection_class):
    from moler.connection import Connection
    import logging

    moler_conn = Connection(name="ABC", logger_name="conn.DEF")
    connection = memory_connection_class(moler_connection=moler_conn)
    assert isinstance(connection.logger, logging.Logger)
    assert connection.logger.name == "conn.DEF.io"


def test_changing_connection_name_doesnt_switch_logger_if_external_logger_used(memory_connection_class):
    from moler.connection import Connection

    moler_conn = Connection()
    connection = memory_connection_class(moler_connection=moler_conn,
                                         name="ABC",
                                         logger_name="conn.ABC")
    assert connection.logger.name == "conn.ABC"
    connection.name = "DEF"
    assert connection.logger.name == "conn.ABC"


def test_changing_connection_name_doesnt_activate_logger_if_logging_is_off(memory_connection_class):
    from moler.connection import Connection

    moler_conn = Connection()
    connection = memory_connection_class(moler_connection=moler_conn,
                                         name="ABC",
                                         logger_name=None)
    assert connection.logger is None
    connection.name = "DEF"
    assert connection.logger is None


def test_changing_connection_name_switches_logger_if_default_logger_used(memory_connection_class):
    from moler.connection import Connection

    # default logger generated internally by connection
    moler_conn = Connection()
    connection = memory_connection_class(moler_connection=moler_conn,
                                         name="ABC")
    assert connection.logger.name == "moler.connection.ABC.io"

    connection.name = "DEF"
    assert connection.logger.name == "moler.connection.DEF.io"

    # default logger via default naming
    moler_conn = Connection()
    connection = memory_connection_class(moler_connection=moler_conn,
                                         name="ABC",
                                         logger_name="moler.connection.ABC.io")
    connection.name = "DEF"
    assert connection.logger.name == "moler.connection.DEF.io"


def test_can_send_and_receive_data_from_connection(memory_connection_without_decoder):
    connection = memory_connection_without_decoder
    moler_conn = connection.moler_connection
    received_data = bytearray()

    def receiver(data, time_recv):
        received_data.extend(data)

    moler_conn.subscribe(receiver, connection_closed_handler)
    with connection.open():
        connection.write(b"command to be echoed")
        connection.read()
        MolerTest.sleep(1)
        assert b'command to be echoed' == received_data

        received_data = bytearray()  # cleanup
        connection.inject([b"async msg1\n", b"async msg2\n"])
        connection.read()
        MolerTest.sleep(1)
        assert b'async msg1\nasync msg2\n' == received_data


def test_will_not_receive_data_from_connection_when_echo_is_off(memory_connection_without_decoder):
    connection = memory_connection_without_decoder
    connection.echo = False
    moler_conn = connection.moler_connection
    received_data = bytearray()

    def receiver(data, time_recv):
        received_data.extend(data)

    moler_conn.subscribe(receiver, connection_closed_handler)
    with connection.open():
        connection.write(b"command to be echoed")
        connection.read()
        assert b'' == received_data


def test_can_inject_data_with_specified_delay(memory_connection_without_decoder):
    connection = memory_connection_without_decoder
    moler_conn = connection.moler_connection
    received_data = bytearray()
    start_time = time.time()

    def receiver(data, time_recv):
        received_data.extend(data)
        if b"msg3" in received_data:
            duration = time.time() - start_time
            assert b'msg1\nmsg2\nmsg3\n' == received_data
            assert (duration > 0.7) and (duration < 0.8)

    moler_conn.subscribe(receiver, connection_closed_handler)
    with connection.open():
        connection.inject(input_bytes=[b"msg1\n", b"msg2\n", b"msg3\n"],
                          delay=0.25)
        connection.read()


def test_inject_response_awaits_nearest_write_before_responding(memory_connection_without_decoder):
    connection = memory_connection_without_decoder
    moler_conn = connection.moler_connection
    received_data = bytearray()

    def receiver(data, time_recv):
        received_data.extend(data)

    moler_conn.subscribe(receiver, connection_closed_handler)
    with connection.open():
        connection.inject_response(input_bytes=[b'response\n'])
        connection.read()
        MolerTest.sleep(1)
        assert b'' == received_data  # injection not active yet
        connection.write(b'request\n')
        connection.read()
        MolerTest.sleep(1)
        assert b'request\nresponse\n' == received_data


def test_can_receive_data_from_ext_io_into_moler_connection(memory_connection):
    connection = memory_connection
    received_data = {'data': ''}  # expecting data decoded into str

    def receiver(data, time_recv):
        received_data['data'] += data

    connection.moler_connection.subscribe(receiver, connection_closed_handler)
    with connection.open():
        connection.write(b"command to be echoed")
        connection.read()
        MolerTest.sleep(1)
        assert 'command to be echoed' == received_data['data']

        received_data = {'data': ''}  # cleanup
        connection.inject(b"async msg")  # can also inject byte-by-byte
        connection.read()
        MolerTest.sleep(1)
        assert 'async msg' == received_data['data']


def test_can_send_data_into_ext_io_from_moler_connection(memory_connection_without_decoder):
    connection = memory_connection_without_decoder
    moler_conn = connection.moler_connection
    received_data = bytearray()

    def receiver(data, time_recv):
        received_data.extend(data)

    moler_conn.subscribe(receiver, connection_closed_handler)
    with connection.open():
        moler_conn.send("command to be echoed")
        connection.read()
        MolerTest.sleep(1)
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
    from moler.threaded_moler_connection import ThreadedMolerConnection
    moler_conn = ThreadedMolerConnection(decoder=lambda data: data.decode("utf-8"),
                                      encoder=lambda data: data.encode("utf-8"))
    connection = connection_class(moler_connection=moler_conn)
    return connection


@pytest.fixture
def memory_connection_without_decoder(memory_connection_class):
    connection_class = memory_connection_class
    from moler.threaded_moler_connection import ThreadedMolerConnection
    moler_conn = ThreadedMolerConnection(encoder=lambda data: data.encode("utf-8"))
    connection = connection_class(moler_connection=moler_conn)
    return connection
