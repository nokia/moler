# -*- coding: utf-8 -*-
"""
Testing external-IO TCP connection

- open/close
- send/receive (naming may differ)
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import time
import importlib
import pytest
import threading
from time import gmtime, strftime


def test_can_open_and_close_connection(tcp_connection_class,
                                       integration_tcp_server_and_pipe):
    """
    Not so atomic test (checks 2 things) but:
    - it is integration tests
    - anyway open needs close as cleanup to not have resources leaking in tests
    """
    from moler.connection import ObservableConnection
    (tcp_server, tcp_server_pipe) = integration_tcp_server_and_pipe

    moler_conn = ObservableConnection()
    print("{}: TCOACC: 1".format(strftime("%Y-%m-%d %H:%M:%S", gmtime())))
    connection = tcp_connection_class(moler_connection=moler_conn, port=tcp_server.port, host=tcp_server.host)
    print("{}: TCOACC: 2".format(strftime("%Y-%m-%d %H:%M:%S", gmtime())))
    connection.open()
    print("{}: TCOACC: 3".format(strftime("%Y-%m-%d %H:%M:%S", gmtime())))
    connection.close()
    print("{}: TCOACC: 4".format(strftime("%Y-%m-%d %H:%M:%S", gmtime())))
    time.sleep(0.01)  # otherwise we have race between server's pipe and from-client-connection
    print("{}: TCOACC: 5".format(strftime("%Y-%m-%d %H:%M:%S", gmtime())))
    tcp_server_pipe.send(("get history", {}))
    print("{}: TCOACC: 6".format(strftime("%Y-%m-%d %H:%M:%S", gmtime())))
    dialog_with_server = tcp_server_pipe.recv()
    print("{}: TCOACC: 7".format(strftime("%Y-%m-%d %H:%M:%S", gmtime())))
    print("dialog with server: '{}'".format(dialog_with_server))
    assert 'Client connected' in dialog_with_server
    assert 'Client disconnected' in dialog_with_server


def test_can_open_and_close_connection_as_context_manager(tcp_connection_class,
                                                          integration_tcp_server_and_pipe):
    from moler.connection import ObservableConnection
    (tcp_server, tcp_server_pipe) = integration_tcp_server_and_pipe

    moler_conn = ObservableConnection()
    connection = tcp_connection_class(moler_connection=moler_conn, port=tcp_server.port, host=tcp_server.host)
    with connection.open():
        pass
    time.sleep(0.1)  # otherwise we have race between server's pipe and from-client-connection
    tcp_server_pipe.send(("get history", {}))
    dialog_with_server = tcp_server_pipe.recv()
    assert 'Client connected' in dialog_with_server
    assert 'Client disconnected' in dialog_with_server


# Note: different external-IO connection may have different naming for their 'send' method
# however, they are uniformed via glueing with moler_connection.send()
# external-IO 'send' method works on bytes; moler_connection performs encoding
def test_can_send_binary_data_over_connection(tcp_connection_class,
                                              integration_tcp_server_and_pipe):
    from moler.connection import ObservableConnection
    (tcp_server, tcp_server_pipe) = integration_tcp_server_and_pipe

    moler_conn = ObservableConnection()  # no decoder, just pass bytes 1:1
    connection = tcp_connection_class(moler_connection=moler_conn, port=tcp_server.port, host=tcp_server.host)
    with connection.open():
        moler_conn.send(data=b'data to be send')
        time.sleep(0.1)  # otherwise we have race between server's pipe and from-client-connection
        tcp_server_pipe.send(("get history", {}))
        dialog_with_server = tcp_server_pipe.recv()
        assert ['Received data:', b'data to be send'] == dialog_with_server[-1]


# Note: different external-IO connection may have different naming for their 'receive' method
# however, they are uniformed via glueing with moler_connection.data_received()
# so, external-IO forwards data to moler_connection.data_received()
# and moler-connection forwards it to anyone subscribed
def test_can_receive_binary_data_from_connection(tcp_connection_class,
                                                 integration_tcp_server_and_pipe):
    from moler.connection import ObservableConnection
    (tcp_server, tcp_server_pipe) = integration_tcp_server_and_pipe
    received_data = bytearray()
    receiver_called = threading.Event()

    def receiver(data):
        received_data.extend(data)
        receiver_called.set()

    moler_conn = ObservableConnection()  # no decoder, just pass bytes 1:1
    moler_conn.subscribe(receiver)       # build forwarding path
    connection = tcp_connection_class(moler_connection=moler_conn, port=tcp_server.port, host=tcp_server.host)
    with connection.open():
        time.sleep(0.1)  # otherwise we have race between server's pipe and from-client-connection
        tcp_server_pipe.send(("send async msg", {'msg': b'data to read'}))
        receiver_called.wait(timeout=0.5)

    assert b'data to read' == received_data


# TODO: tests for error cases raising Exceptions
# --------------------------- resources ---------------------------


@pytest.fixture(params=['io.raw.tcp.ThreadedTcp'])
def tcp_connection_class(request):
    module_name, class_name = request.param.rsplit('.', 1)
    module = importlib.import_module('moler.{}'.format(module_name))
    connection_class = getattr(module, class_name)
    return connection_class

@pytest.yield_fixture()
def integration_tcp_server_and_pipe():
    from moler.io.raw.tcpserverpiped import tcp_server_piped
    with tcp_server_piped(use_stderr_logger=True) as server_and_pipe:
        (server, svr_ctrl_pipe) = server_and_pipe
        yield (server, svr_ctrl_pipe)
