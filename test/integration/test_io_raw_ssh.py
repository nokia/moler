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
    # connection = ssh_connection_class(moler_connection=moler_conn, port=22, host='localhost', port=22, username='molerssh', password='moler_password')
    # TODO - let it be runable on any CI machine - need SSH server in test
    connection = ssh_connection_class(host='localhost', port=22, username='molerssh', password='moler_password')
    assert connection.ssh_client.get_transport() is None
    assert connection.shell_channel is None

    connection.open()
    assert connection.ssh_client.get_transport() is not None
    assert connection.shell_channel is not None
    assert connection.ssh_client.get_transport() == connection.shell_channel.get_transport()
    assert connection.shell_channel.get_transport().is_active()
    assert connection.shell_channel.get_transport().is_authenticated()

    connection.close()
    assert connection.ssh_client.get_transport() is None


def test_can_open_and_close_connection_as_context_manager(ssh_connection_class):

    connection = ssh_connection_class(host='localhost', port=22, username='molerssh', password='moler_password')
    with connection.open():
        assert connection.shell_channel.get_transport().is_authenticated()
    assert connection.ssh_client.get_transport() is None

    with connection:
        assert connection.shell_channel.get_transport().is_authenticated()
    assert connection.ssh_client.get_transport() is None


# Note1: different external-IO connection may have different naming for their 'send' method
# however, they are uniformed via glueing with moler_connection.send()
# external-IO 'send' method works on bytes; moler_connection performs encoding
# Note2: we check sending and receiving together - checking send by its result on receive
def test_can_send_and_receive_binary_data_over_connection(ssh_connection_class):

    connection = ssh_connection_class(host='localhost', port=22, username='molerssh', password='moler_password')
    with connection.open():
        time.sleep(0.1)
        if connection.shell_channel.recv_ready():  # some banner just after open ssh
            resp_bytes1 = connection.receive()
        #moler_conn.send(data=b'data to be send')
        request = "pwd\n"
        bytes2send = request.encode("utf-8")
        connection.send(bytes2send)
        time.sleep(0.1)
        resp_bytes = connection.receive()
        response = resp_bytes.decode("utf-8")
        assert '/home/' in response


def test_cant_send_over_not_opened_connection(ssh_connection_class):
    from moler.io.io_exceptions import RemoteEndpointNotConnected
    connection = ssh_connection_class(host='localhost', port=22, username='molerssh', password='moler_password')
    with pytest.raises(RemoteEndpointNotConnected):
        connection.send(b'ls -l\n')


def test_cant_receive_from_not_opened_connection(ssh_connection_class):
    from moler.io.io_exceptions import RemoteEndpointNotConnected
    connection = ssh_connection_class(host='localhost', port=22, username='molerssh', password='moler_password')
    with pytest.raises(RemoteEndpointNotConnected):
        connection.receive()


def test_receive_is_timeout_protected(ssh_connection_class):
    from moler.io.io_exceptions import ConnectionTimeout
    connection = ssh_connection_class(host='localhost', port=22, username='molerssh', password='moler_password')
    with connection.open():
        time.sleep(0.1)
        if connection.shell_channel.recv_ready():  # some banner just after open ssh
            connection.receive()
        with pytest.raises(ConnectionTimeout) as exc:
            connection.receive(timeout=0.2)
        assert "Timeout (> 0.200 sec) on ssh://molerssh@localhost:22" in str(exc.value)


def test_receive_detects_remote_end_close(ssh_connection_class):
    from moler.io.io_exceptions import RemoteEndpointDisconnected
    connection = ssh_connection_class(host='localhost', port=22, username='molerssh', password='moler_password')
    with connection.open():
        time.sleep(0.1)
        if connection.shell_channel.recv_ready():  # some banner just after open ssh
            connection.receive()
        request = "exit\n"
        bytes2send = request.encode("utf-8")
        connection.send(bytes2send)
        time.sleep(0.1)
        echo_bytes = connection.receive(timeout=0.5)
        echo = echo_bytes.decode("utf-8")
        assert "exit" in echo
        with pytest.raises(RemoteEndpointDisconnected):
            connection.receive(timeout=0.5)
        assert connection.shell_channel is None
        assert connection.ssh_client.get_transport() is None


# --------------------------- resources ---------------------------


@pytest.fixture(params=['io.raw.sshshell.SshShell'])
def ssh_connection_class(request):
    module_name, class_name = request.param.rsplit('.', 1)
    module = importlib.import_module('moler.{}'.format(module_name))
    connection_class = getattr(module, class_name)
    return connection_class
