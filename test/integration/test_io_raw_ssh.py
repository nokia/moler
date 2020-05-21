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
import mock
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


def test_connection_created_from_existing_open_connection_reuses_its_transport(ssh_connection_class):

    connection = ssh_connection_class(host='localhost', port=22, username='molerssh', password='moler_password')
    with connection.open():
        # no host, port, username, password since we want to create another connection to new shell
        # towards same host/port using same credentials
        reused_transport = connection.ssh_client.get_transport()
        new_connection = ssh_connection_class.from_sshshell(sshshell=connection)

        assert reused_transport is new_connection.ssh_client.get_transport()

        assert new_connection.ssh_client.get_transport().is_authenticated()  # new one is authenticated
        assert new_connection.shell_channel is None  # but not open yet (no shell on remote)
        with new_connection.open():
            assert new_connection.shell_channel is not None
            assert new_connection.ssh_client.get_transport() is new_connection.shell_channel.get_transport()

            assert reused_transport is new_connection.ssh_client.get_transport()

            assert connection.shell_channel.get_transport().is_active()
            assert connection.shell_channel.get_transport().is_authenticated()


def test_logging_of_open_and_close_connection(ssh_connection_class):
    class MyLogger(object):
        def __init__(self):
            self.calls = []

        def debug(self, msg):
            self.calls.append(("DEBUG", msg))

        def info(self, msg):
            self.calls.append(("INFO", msg))

    logger = MyLogger()
    connection = ssh_connection_class(host='localhost', port=22, username='molerssh', password='moler_password',
                                      logger=logger)
    with connection.open():
        new_connection = ssh_connection_class.from_sshshell(sshshell=connection, logger=logger)
        with new_connection.open():
            pass
    assert logger.calls[0] == ('DEBUG', 'connecting to ssh://molerssh@localhost:22')
    assert logger.calls[1][0] == 'DEBUG'
    assert 'established ssh transport to localhost:22' in logger.calls[1][1]
    assert logger.calls[2][0] == 'DEBUG'
    assert 'established shell ssh to localhost:22 [channel 0]' in logger.calls[2][1]
    assert logger.calls[3] == ('INFO', 'connection ssh://molerssh@localhost:22 [channel 0] is open')
    assert logger.calls[4] == ('DEBUG', 'connecting to ssh://molerssh@localhost:22')
    assert logger.calls[5][0] == 'DEBUG'
    assert 'reusing ssh transport to localhost:22' in logger.calls[5][1]
    assert logger.calls[6][0] == 'DEBUG'
    assert 'established shell ssh to localhost:22 [channel 1]' in logger.calls[6][1]
    assert logger.calls[7] == ('INFO', 'connection ssh://molerssh@localhost:22 [channel 1] is open')
    assert logger.calls[8] == ('DEBUG', 'closing ssh://molerssh@localhost:22 [channel 1]')
    assert logger.calls[9][0] == 'DEBUG'
    assert 'closed shell ssh to localhost:22 [channel 1]' in logger.calls[9][1]
    assert logger.calls[10] == ('INFO', 'connection ssh://molerssh@localhost:22 [channel 1] is closed')
    assert logger.calls[11] == ('DEBUG', 'closing ssh://molerssh@localhost:22 [channel 0]')
    assert logger.calls[12][0] == 'DEBUG'
    assert 'closed shell ssh to localhost:22 [channel 0]' in logger.calls[12][1]
    assert logger.calls[13][0] == 'DEBUG'
    assert 'closing ssh transport to localhost:22' in logger.calls[13][1]
    assert logger.calls[10] == ('INFO', 'connection ssh://molerssh@localhost:22 [channel 1] is closed')


def test_opening_connection_created_from_existing_one_is_quicker(ssh_connection_class):

    connection = ssh_connection_class(host='localhost', port=22, username='molerssh', password='moler_password')
    start1 = time.time()
    with connection.open():
        end1 = time.time()
        new_connection = ssh_connection_class.from_sshshell(sshshell=connection)
        start2 = time.time()
        with new_connection.open():
            end2 = time.time()
    full_open_duration = end1 - start1
    reused_conn_open_duration = end2 - start2
    assert reused_conn_open_duration < (0.1 * full_open_duration)


def test_closing_connection_created_from_existing_one_is_not_closing_transport_till_last_channel(ssh_connection_class):

    connection = ssh_connection_class(host='localhost', port=22, username='molerssh', password='moler_password')
    with connection.open():
        new_connection = ssh_connection_class.from_sshshell(sshshell=connection)
        with new_connection.open():
            assert connection.shell_channel.get_transport().is_authenticated()
            assert new_connection.shell_channel.get_transport().is_authenticated()
        assert new_connection.shell_channel is None
        assert connection.shell_channel is not None
        assert connection.shell_channel.get_transport().is_authenticated()
    assert connection.shell_channel is None


def test_str_representation_of_connection(ssh_connection_class):

    connection = ssh_connection_class(host='localhost', port=22, username='molerssh', password='moler_password')
    assert str(connection) == "ssh://molerssh@localhost:22"
    with connection.open():
        shell_channel_id = connection.shell_channel.get_id()
        assert str(connection) == "ssh://molerssh@localhost:22 [channel {}]".format(shell_channel_id)
    assert str(connection) == "ssh://molerssh@localhost:22"


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


def test_send_can_timeout(ssh_connection_class):
    from moler.io.io_exceptions import ConnectionTimeout
    connection = ssh_connection_class(host='localhost', port=22, username='molerssh', password='moler_password')
    with connection.open():
        time.sleep(0.1)
        if connection.shell_channel.recv_ready():  # some banner just after open ssh
            connection.receive()
        with pytest.raises(ConnectionTimeout) as exc:
            big_data = "123456789 " * 10000
            request = "echo {}\n".format(big_data)
            bytes2send = request.encode("utf-8")
            connection.send(bytes2send, timeout=0.001)
        assert "Timeout (> 0.001 sec) on ssh://molerssh@localhost:22" in str(exc.value)


def test_send_can_push_remaining_data_within_timeout(ssh_connection_class):
    connection = ssh_connection_class(host='localhost', port=22, username='molerssh', password='moler_password')
    with connection.open():
        time.sleep(0.1)
        if connection.shell_channel.recv_ready():  # some banner just after open ssh
            connection.receive()

        big_data = "123456789 " * 10000
        request = "echo {}\n".format(big_data)
        bytes2send = request.encode("utf-8")

        data_chunks_len = []
        original_send = connection.shell_channel.send

        def send_counting_chunks(data):
            nb_bytes_sent = original_send(data)
            data_chunks_len.append(nb_bytes_sent)
            return nb_bytes_sent

        with mock.patch.object(connection.shell_channel, "send", send_counting_chunks):
            connection.send(bytes2send, timeout=0.1)
        assert len(data_chunks_len) > 1  # indeed, there were chunks
        assert sum(data_chunks_len) == len(bytes2send)


def test_send_detects_remote_end_closed(ssh_connection_class):
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
            connection.send(bytes2send)
        assert connection.shell_channel is None
        assert connection.ssh_client.get_transport() is None

# --------------------------- resources ---------------------------


@pytest.fixture(params=['io.raw.sshshell.SshShell'])
def ssh_connection_class(request):
    module_name, class_name = request.param.rsplit('.', 1)
    module = importlib.import_module('moler.{}'.format(module_name))
    connection_class = getattr(module, class_name)
    return connection_class
