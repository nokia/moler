# -*- coding: utf-8 -*-
"""
Testing external-IO SSH connection

- open/close
- send/receive (naming may differ)
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'


import time
import importlib
import pytest
import threading


def test_can_open_and_close_connection(ssh_connection_class):
    """
    Not so atomic test (checks 2 things) but:
    - it is integration tests
    - anyway open needs close as cleanup to not have resources leaking in tests
    """
    from moler.threaded_moler_connection import ThreadedMolerConnection

    #moler_conn = ThreadedMolerConnection()
    # connection = ssh_connection_class(moler_connection=moler_conn, port=22, host='localhost', port=22, username='ute', password='ute')
    connection = ssh_connection_class(host='localhost', port=22, username='ute', password='ute')
    assert connection.ssh_client.get_transport() is None
    assert connection.shell_channel is None

    connection.open()
    assert connection.ssh_client.get_transport() is not None
    assert connection.shell_channel is not None
    assert connection.ssh_client.get_transport() == connection.shell_channel.get_transport()
    assert connection.shell_channel.get_transport().is_active()
    assert connection.shell_channel.get_transport().is_authenticated()
    assert ('127.0.0.1', 22) == connection.shell_channel.get_transport().getpeername()

    connection.close()
    assert connection.ssh_client.get_transport() is None



# def test_can_open_and_close_connection_as_context_manager(tcp_connection_class,
#                                                           integration_tcp_server_and_pipe):
#     from moler.threaded_moler_connection import ThreadedMolerConnection
#     (tcp_server, tcp_server_pipe) = integration_tcp_server_and_pipe
#
#     moler_conn = ThreadedMolerConnection()
#     connection = tcp_connection_class(moler_connection=moler_conn, port=tcp_server.port, host=tcp_server.host)
#     with connection.open():
#         pass
#     dialog_with_server = _wait_for_last_message(tcp_server_pipe=tcp_server_pipe, last_message='Client disconnected',
#                                                 timeout=5)
#     assert 'Client connected' in dialog_with_server
#     assert 'Client disconnected' in dialog_with_server


# --------------------------- resources ---------------------------


@pytest.fixture(params=['io.raw.ssh.Ssh'])
def ssh_connection_class(request):
    module_name, class_name = request.param.rsplit('.', 1)
    module = importlib.import_module('moler.{}'.format(module_name))
    connection_class = getattr(module, class_name)
    return connection_class
