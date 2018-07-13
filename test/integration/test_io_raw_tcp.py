# -*- coding: utf-8 -*-
"""
Testing external-IO TCP connection

- open/close
- send/receive (naming may differ)
"""
import time

import pytest

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'


def test_can_open_and_close_connection(tcp_connection_class,
                                       integration_tcp_server_and_pipe):
    """
    Not so atomic test (checks 2 things) but:
    - it is integration tests
    - anyway open needs close as cleanup to not have resources leaking in tests
    """
    (tcp_server, tcp_server_pipe) = integration_tcp_server_and_pipe

    connection = tcp_connection_class(port=tcp_server.port, host=tcp_server.host)
    connection.open()
    connection.close()
    time.sleep(0.1)  # otherwise we have race between server's pipe and from-client-connection
    tcp_server_pipe.send(("get history", {}))
    dialog_with_server = tcp_server_pipe.recv()
    assert 'Client connected' in dialog_with_server
    assert 'Client disconnected' in dialog_with_server


def test_can_open_and_close_connection_as_context_manager(tcp_connection_class,
                                                          integration_tcp_server_and_pipe):
    (tcp_server, tcp_server_pipe) = integration_tcp_server_and_pipe

    connection = tcp_connection_class(port=tcp_server.port, host=tcp_server.host)
    with connection:
        pass
    time.sleep(0.1)  # otherwise we have race between server's pipe and from-client-connection
    tcp_server_pipe.send(("get history", {}))
    dialog_with_server = tcp_server_pipe.recv()
    assert 'Client connected' in dialog_with_server
    assert 'Client disconnected' in dialog_with_server


# TODO: parametrize - different external-IO connection may have
# TODO:               different naming for their 'send' method
def test_can_send_data_over_connection(tcp_connection_class,
                                       integration_tcp_server_and_pipe):
    (tcp_server, tcp_server_pipe) = integration_tcp_server_and_pipe

    connection = tcp_connection_class(port=tcp_server.port, host=tcp_server.host)
    connection.open()
    connection.send(data=b'data to be send')
    time.sleep(0.1)  # otherwise we have race between server's pipe and from-client-connection
    tcp_server_pipe.send(("get history", {}))
    dialog_with_server = tcp_server_pipe.recv()
    assert ['Received data:', b'data to be send'] == dialog_with_server[-1]
    connection.close()


# TODO: parametrize - different external-IO connection may have
# TODO:               different naming for their 'rceive' method
def test_can_receive_data_from_connection(tcp_connection_class,
                                          integration_tcp_server_and_pipe):
    (tcp_server, tcp_server_pipe) = integration_tcp_server_and_pipe

    connection = tcp_connection_class(port=tcp_server.port, host=tcp_server.host)
    connection.open()
    time.sleep(0.1)  # otherwise we have race between server's pipe and from-client-connection
    tcp_server_pipe.send(("send async msg", {'msg': b'data to read'}))
    received_data = connection.receive()
    connection.close()
    assert b'data to read' == received_data


# TODO: tests for error cases raising Exceptions
# --------------------------- resources ---------------------------


@pytest.fixture()
def tcp_connection_class():
    from moler.io.raw.tcp import Tcp
    return Tcp


@pytest.yield_fixture()
def integration_tcp_server_and_pipe():
    from moler.io.raw.tcpserverpiped import tcp_server_piped
    with tcp_server_piped(use_stderr_logger=True) as server_and_pipe:
        (server, svr_ctrl_pipe) = server_and_pipe
        yield (server, svr_ctrl_pipe)
