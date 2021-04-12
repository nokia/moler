# -*- coding: utf-8 -*-
"""
Testing external-IO TCP connection

- open/close
- send/receive (naming may differ)
"""

__author__ = 'Grzegorz Latuszek, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2021, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com'


import time
import importlib
import pytest
import threading
import sys


python3_only = pytest.mark.skipif(sys.version_info < (3, 0),
                                  reason="Not stable under Python2 which is no more supported.")


@python3_only()
def test_can_open_and_close_connection(tcp_connection_class,
                                       integration_tcp_server_and_pipe):
    """
    Not so atomic test (checks 2 things) but:
    - it is integration tests
    - anyway open needs close as cleanup to not have resources leaking in tests
    """
    from moler.threaded_moler_connection import ThreadedMolerConnection
    (tcp_server, tcp_server_pipe) = integration_tcp_server_and_pipe

    moler_conn = ThreadedMolerConnection()
    connection = tcp_connection_class(moler_connection=moler_conn, port=tcp_server.port, host=tcp_server.host)
    connection.open()
    connection.close()
    dialog_with_server = _wait_for_last_message(tcp_server_pipe=tcp_server_pipe, last_message='Client disconnected',
                                                timeout=5)
    assert 'Client connected' in dialog_with_server
    assert 'Client disconnected' in dialog_with_server


@python3_only()
def test_can_open_and_close_connection_as_context_manager(tcp_connection_class,
                                                          integration_tcp_server_and_pipe):
    from moler.threaded_moler_connection import ThreadedMolerConnection
    (tcp_server, tcp_server_pipe) = integration_tcp_server_and_pipe

    moler_conn = ThreadedMolerConnection()
    connection = tcp_connection_class(moler_connection=moler_conn, port=tcp_server.port, host=tcp_server.host)
    with connection.open():
        pass
    dialog_with_server = _wait_for_last_message(tcp_server_pipe=tcp_server_pipe, last_message='Client disconnected',
                                                timeout=5)
    assert 'Client connected' in dialog_with_server
    assert 'Client disconnected' in dialog_with_server


# Note: different external-IO connection may have different naming for their 'send' method
# however, they are uniformed via glueing with moler_connection.send()
# external-IO 'send' method works on bytes; moler_connection performs encoding
@python3_only()
def test_can_send_binary_data_over_connection(tcp_connection_class,
                                              integration_tcp_server_and_pipe):
    from moler.threaded_moler_connection import ThreadedMolerConnection
    (tcp_server, tcp_server_pipe) = integration_tcp_server_and_pipe

    moler_conn = ThreadedMolerConnection()  # no decoder, just pass bytes 1:1
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
@python3_only()
def test_can_receive_binary_data_from_connection(tcp_connection_class,
                                                 integration_tcp_server_and_pipe):
    from moler.threaded_moler_connection import ThreadedMolerConnection
    (tcp_server, tcp_server_pipe) = integration_tcp_server_and_pipe
    received_data = bytearray()
    receiver_called = threading.Event()

    def receiver(data, timestamp):
        received_data.extend(data)
        receiver_called.set()

    def connection_closed_handler():
        pass

    moler_conn = ThreadedMolerConnection()  # no decoder, just pass bytes 1:1
    moler_conn.subscribe(receiver, connection_closed_handler)       # build forwarding path
    connection = tcp_connection_class(moler_connection=moler_conn, port=tcp_server.port, host=tcp_server.host)
    with connection.open():
        time.sleep(0.1)  # otherwise we have race between server's pipe and from-client-connection
        tcp_server_pipe.send(("send async msg", {'msg': b'data to read'}))
        receiver_called.wait(timeout=0.5)

    assert b'data to read' == received_data


# TODO: tests for error cases raising Exceptions
# --------------------------- resources ---------------------------


def _wait_for_last_message(tcp_server_pipe, last_message="Client disconnected", timeout=5):
    start_time = time.time()
    dialog_with_server = []

    while last_message not in dialog_with_server:
        tcp_server_pipe.send(("get history", {}))
        time.sleep(0.01)
        dialog_with_server = tcp_server_pipe.recv()

        if time.time() - start_time > timeout:
            break

    return dialog_with_server


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
