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


def test_can_create_passive_sshshell_connection_using_same_api(passive_sshshell_connection_class):
    # sshshell active and passive connections differ in API.
    # but we want to have all connections of class 'passive sshshell' to have same API

    connection = passive_sshshell_connection_class(host='localhost', port=22,
                                                   username='molerssh', password='moler_password')
    assert connection.ssh_transport is None
    assert connection.shell_channel is None
    assert hasattr(connection, "receive")


def test_can_create_active_sshshell_connection_using_same_api(active_sshshell_connection_class):
    # we want to have all connections of class 'active sshshell' to share same API

    from moler.threaded_moler_connection import ThreadedMolerConnection

    moler_conn = ThreadedMolerConnection(decoder=lambda data: data.decode("utf-8"),
                                         encoder=lambda data: data.encode("utf-8"))

    connection = active_sshshell_connection_class(moler_connection=moler_conn,
                                                  host='localhost', port=22,
                                                  username='molerssh', password='moler_password')
    assert connection.ssh_transport is None
    assert connection.shell_channel is None
    assert hasattr(connection, "data_received")


def test_can_open_and_close_connection(sshshell_connection):
    """
    Not so atomic test (checks 2 things) but:
    - it is integration tests
    - anyway open needs close as cleanup to not have resources leaking in tests
    """
    connection = sshshell_connection

    connection.open()
    assert connection.ssh_transport is not None
    assert connection.shell_channel is not None
    assert connection.ssh_transport == connection.shell_channel.get_transport()
    assert connection.ssh_transport.is_active()
    assert connection.ssh_transport.is_authenticated()

    connection.close()
    assert connection.shell_channel is None
    assert connection.ssh_transport is None


def test_can_open_and_close_connection_as_context_manager(sshshell_connection):

    connection = sshshell_connection
    with connection.open():
        assert connection.ssh_transport.is_authenticated()
        assert connection.shell_channel is not None
    assert connection.ssh_transport is None
    assert connection.shell_channel is None

    with connection:
        assert connection.ssh_transport.is_authenticated()
        assert connection.shell_channel is not None
    assert connection.ssh_transport is None
    assert connection.shell_channel is None


def test_passive_connection_created_from_existing_open_connection_reuses_its_transport(passive_sshshell_connection_class):

    source_connection = passive_sshshell_connection_class(host='localhost', port=22,
                                                          username='molerssh', password='moler_password')
    with source_connection.open():
        source_transport = source_connection.ssh_transport
        # no host, port, username, password since we want to create another connection to new shell
        # towards same host/port using same credentials
        new_connection = passive_sshshell_connection_class.from_sshshell(sshshell=source_connection)

        assert source_transport is new_connection.ssh_transport

        assert new_connection.ssh_transport.is_authenticated()  # new one is authenticated
        assert new_connection.shell_channel is None  # but not open yet (no shell on remote)
        with new_connection.open():
            assert new_connection.shell_channel is not None
            assert source_transport is new_connection.ssh_transport  # no change after open()


def test_passive_connection_created_from_existing_nonopen_connection_will_share_same_transport(passive_sshshell_connection_class):

    source_connection = passive_sshshell_connection_class(host='localhost', port=22,
                                                          username='molerssh', password='moler_password')
    assert source_connection.ssh_transport is None
    new_connection = passive_sshshell_connection_class.from_sshshell(sshshell=source_connection)
    with source_connection.open():
        source_transport = source_connection.ssh_transport

        assert source_transport is new_connection.ssh_transport

        assert new_connection.ssh_transport.is_authenticated()  # new one is authenticated
        assert new_connection.shell_channel is None  # but not open yet (no shell on remote)
        with new_connection.open():
            assert new_connection.shell_channel is not None
            assert source_transport is new_connection.ssh_transport  # no change after open()


def test_active_connection_created_from_existing_open_connection_reuses_its_transport(active_sshshell_connection_class):
    from moler.threaded_moler_connection import ThreadedMolerConnection

    moler_conn = ThreadedMolerConnection(decoder=lambda data: data.decode("utf-8"),
                                         encoder=lambda data: data.encode("utf-8"))
    another_moler_conn = ThreadedMolerConnection(decoder=lambda data: data.decode("utf-8"),
                                                 encoder=lambda data: data.encode("utf-8"))

    source_connection = active_sshshell_connection_class(moler_connection=moler_conn,
                                                         host='localhost', port=22,
                                                         username='molerssh', password='moler_password')
    with source_connection.open():
        source_transport = source_connection.ssh_transport

        # no host, port, username, password since we want to create another connection to new shell
        # towards same host/port using same credentials
        ##################################################################################
        # CAUTION: they should not share same moler connection (hoever, it is not blocked)
        #          If they do you should be aware what you are doing
        #          You are multiplexing io-streams into single moler-connection
        ##################################################################################
        new_connection = active_sshshell_connection_class.from_sshshell(sshshell=source_connection,
                                                                        moler_connection=another_moler_conn)

        assert source_transport is new_connection.ssh_transport

        assert new_connection.ssh_transport.is_authenticated()  # new one is authenticated
        assert new_connection.shell_channel is None  # but not open yet (no shell on remote)
        with new_connection.open():
            assert new_connection.shell_channel is not None
            assert source_transport is new_connection.ssh_transport  # no change after open()


def test_active_connection_created_from_existing_nonopen_connection_will_share_same_transport(sshshell_connection,
                                                                                              active_sshshell_connection_class):
    from moler.threaded_moler_connection import ThreadedMolerConnection

    new_moler_conn = ThreadedMolerConnection(decoder=lambda data: data.decode("utf-8"),
                                             encoder=lambda data: data.encode("utf-8"))

    source_connection = sshshell_connection  # source might be either passive or active
    assert source_connection.ssh_transport is None
    new_connection = active_sshshell_connection_class.from_sshshell(sshshell=source_connection,
                                                                    moler_connection=new_moler_conn)
    with source_connection.open():
        source_transport = source_connection.ssh_transport

        assert source_transport is new_connection.ssh_transport

        assert new_connection.ssh_transport.is_authenticated()  # new one is authenticated
        assert new_connection.shell_channel is None  # but not open yet (no shell on remote)
        with new_connection.open():
            assert new_connection.shell_channel is not None
            assert source_transport is new_connection.ssh_transport  # no change after open()


def test_logging_for_open_close_of_passive_connection(passive_sshshell_connection_class, mocked_logger):
    logger = mocked_logger
    connection = passive_sshshell_connection_class(host='localhost', port=22,
                                                   username='molerssh', password='moler_password',
                                                   logger=logger)
    with connection.open():
        new_connection = passive_sshshell_connection_class.from_sshshell(sshshell=connection, logger=logger)
        with new_connection.open():
            pass
    assert logger.calls == ['DEBUG: connecting to ssh://molerssh@localhost:22',
                            'DEBUG:   established ssh transport to localhost:22',
                            'DEBUG:   established shell ssh to localhost:22 [channel 0]',
                            ' INFO: connection ssh://molerssh@localhost:22 [channel 0] is open',
                            'DEBUG: connecting to ssh://molerssh@localhost:22',
                            'DEBUG:   reusing ssh transport to localhost:22',
                            'DEBUG:   established shell ssh to localhost:22 [channel 1]',
                            ' INFO: connection ssh://molerssh@localhost:22 [channel 1] is open',
                            'DEBUG: closing ssh://molerssh@localhost:22 [channel 1]',
                            'DEBUG:   closed shell ssh to localhost:22 [channel 1]',
                            ' INFO: connection ssh://molerssh@localhost:22 [channel 1] is closed',
                            'DEBUG: closing ssh://molerssh@localhost:22 [channel 0]',
                            'DEBUG:   closed shell ssh to localhost:22 [channel 0]',
                            'DEBUG:   closing ssh transport to localhost:22',
                            ' INFO: connection ssh://molerssh@localhost:22 [channel 0] is closed']


def test_logging_for_open_close_of_active_connection(active_sshshell_connection_class, mocked_logger):
    from moler.threaded_moler_connection import ThreadedMolerConnection

    logger = mocked_logger
    moler_conn = ThreadedMolerConnection(decoder=lambda data: data.decode("utf-8"),
                                         encoder=lambda data: data.encode("utf-8"))
    another_moler_conn = ThreadedMolerConnection(decoder=lambda data: data.decode("utf-8"),
                                                 encoder=lambda data: data.encode("utf-8"))
    connection = active_sshshell_connection_class(moler_connection=moler_conn,
                                                  host='localhost', port=22,
                                                  username='molerssh', password='moler_password',
                                                  logger=logger)
    with connection.open():
        new_connection = active_sshshell_connection_class.from_sshshell(sshshell=connection,
                                                                        moler_connection=another_moler_conn,
                                                                        logger=logger)
        with new_connection.open():
            pass
    assert logger.calls == ['DEBUG: connecting to ssh://molerssh@localhost:22',
                            'DEBUG:   established ssh transport to localhost:22',
                            'DEBUG:   established shell ssh to localhost:22 [channel 0]',
                            ' INFO: connection ssh://molerssh@localhost:22 [channel 0] is open',
                            'DEBUG: connecting to ssh://molerssh@localhost:22',
                            'DEBUG:   reusing ssh transport to localhost:22',
                            'DEBUG:   established shell ssh to localhost:22 [channel 1]',
                            ' INFO: connection ssh://molerssh@localhost:22 [channel 1] is open',
                            'DEBUG: closing ssh://molerssh@localhost:22 [channel 1]',
                            'DEBUG:   closed shell ssh to localhost:22 [channel 1]',
                            ' INFO: connection ssh://molerssh@localhost:22 [channel 1] is closed',
                            'DEBUG: closing ssh://molerssh@localhost:22 [channel 0]',
                            'DEBUG:   closed shell ssh to localhost:22 [channel 0]',
                            'DEBUG:   closing ssh transport to localhost:22',
                            ' INFO: connection ssh://molerssh@localhost:22 [channel 0] is closed']


def test_opening_connection_created_from_existing_one_is_quicker(sshshell_connection):
    from moler.threaded_moler_connection import ThreadedMolerConnection

    connection = sshshell_connection
    start1 = time.time()
    with connection.open():
        end1 = time.time()
        if hasattr(connection, "moler_connection"):  # active connection
            another_moler_conn = ThreadedMolerConnection(decoder=lambda data: data.decode("utf-8"),
                                                         encoder=lambda data: data.encode("utf-8"))
            new_connection = sshshell_connection.__class__.from_sshshell(moler_connection=another_moler_conn,
                                                                         sshshell=connection)
        else:
            new_connection = sshshell_connection.__class__.from_sshshell(sshshell=connection)
        start2 = time.time()
        with new_connection.open():
            end2 = time.time()
    full_open_duration = end1 - start1
    reused_conn_open_duration = end2 - start2
    assert (reused_conn_open_duration * 5 ) < full_open_duration


def test_closing_connection_created_from_existing_one_is_not_closing_transport_till_last_channel(sshshell_connection):
    from moler.threaded_moler_connection import ThreadedMolerConnection

    connection = sshshell_connection
    with connection.open():
        if hasattr(connection, "moler_connection"):  # active connection
            another_moler_conn = ThreadedMolerConnection(decoder=lambda data: data.decode("utf-8"),
                                                         encoder=lambda data: data.encode("utf-8"))
            new_connection = sshshell_connection.__class__.from_sshshell(moler_connection=another_moler_conn,
                                                                         sshshell=connection)
        else:
            new_connection = sshshell_connection.__class__.from_sshshell(sshshell=connection)
        with new_connection.open():
            assert connection.shell_channel.get_transport().is_authenticated()
            assert new_connection.shell_channel.get_transport().is_authenticated()
        assert new_connection.shell_channel is None
        assert connection.shell_channel is not None
        assert connection.shell_channel.get_transport().is_authenticated()
    assert connection.shell_channel is None


def test_str_representation_of_connection(sshshell_connection):
    from moler.threaded_moler_connection import ThreadedMolerConnection

    if hasattr(sshshell_connection, "moler_connection"):  # active connection
        another_moler_conn = ThreadedMolerConnection(decoder=lambda data: data.decode("utf-8"),
                                                     encoder=lambda data: data.encode("utf-8"))
        connection = sshshell_connection.__class__(moler_connection=another_moler_conn,
                                                   host='localhost', port=22,
                                                   username='molerssh', password='moler_password')
    else:
        connection = sshshell_connection.__class__(host='localhost', port=22,
                                                   username='molerssh', password='moler_password')
    assert str(connection) == "ssh://molerssh@localhost:22"
    with connection.open():
        shell_channel_id = connection.shell_channel.get_id()
        assert str(connection) == "ssh://molerssh@localhost:22 [channel {}]".format(shell_channel_id)
    assert str(connection) == "ssh://molerssh@localhost:22"


# Note1: different external-IO connection may have different naming for their 'send' method
# however, they are uniformed via glueing with moler_connection.send()
# external-IO 'send' method works on bytes; moler_connection performs encoding
# Note2: we check sending and receiving together - checking send by its result on receive
def test_can_send_and_receive_binary_data_over_connection(passive_sshshell_connection_class):

    connection = passive_sshshell_connection_class(host='localhost', port=22, username='molerssh', password='moler_password')
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


def test_cant_send_over_not_opened_connection(sshshell_connection):
    from moler.io.io_exceptions import RemoteEndpointNotConnected
    connection = sshshell_connection
    with pytest.raises(RemoteEndpointNotConnected):
        connection.send(b'ls -l\n')


def test_cant_receive_from_not_opened_connection(sshshell_connection):
    from moler.io.io_exceptions import RemoteEndpointNotConnected
    connection = sshshell_connection
    with pytest.raises(RemoteEndpointNotConnected):
        connection.receive()


def test_receive_is_timeout_protected(passive_sshshell_connection_class):
    from moler.io.io_exceptions import ConnectionTimeout
    connection = passive_sshshell_connection_class(host='localhost', port=22, username='molerssh', password='moler_password')
    with connection.open():
        time.sleep(0.3)
        if connection.shell_channel.recv_ready():  # some banner just after open ssh
            connection.receive()
        with pytest.raises(ConnectionTimeout) as exc:
            connection.receive(timeout=0.2)
        assert "Timeout (> 0.200 sec) on ssh://molerssh@localhost:22" in str(exc.value)


def test_receive_detects_remote_end_close(passive_sshshell_connection_class):
    from moler.io.io_exceptions import RemoteEndpointDisconnected
    connection = passive_sshshell_connection_class(host='localhost', port=22, username='molerssh', password='moler_password')
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
        assert connection.ssh_transport is None


def test_send_can_timeout(sshshell_connection):
    from moler.io.io_exceptions import ConnectionTimeout
    connection = sshshell_connection
    with connection.open():
        with pytest.raises(ConnectionTimeout) as exc:
            big_data = "123456789 " * 10000
            request = "echo {}\n".format(big_data)
            bytes2send = request.encode("utf-8")
            connection.send(bytes2send, timeout=0.001)
        assert "Timeout (> 0.001 sec) on ssh://molerssh@localhost:22" in str(exc.value)


def test_send_can_push_remaining_data_within_timeout(sshshell_connection):
    connection = sshshell_connection
    with connection.open():
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


def test_send_detects_remote_end_closed(passive_sshshell_connection_class):
    from moler.io.io_exceptions import RemoteEndpointDisconnected
    connection = passive_sshshell_connection_class(host='localhost', port=22, username='molerssh', password='moler_password')
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
        assert connection.ssh_transport is None

#
# def test_threaded_sshshell_send_detects_remote_end_closed(active_sshshell_connection_class):
#     from moler.io.io_exceptions import RemoteEndpointDisconnected
#     from moler.io.raw.sshshell import ThreadedSshShell
#     received_data = [b'']
#     receiver_called = threading.Event()
#
#     def receiver(data, timestamp):
#         print(">>>>" + data)
#         received_data[0] = data
#         if "exit" in received_data.decode("utf-8"):
#             receiver_called.set()
#
#     def connection_closed_handler():
#         pass
#
#     connection = sshshell_connection
#     with connection.open():
#         time.sleep(0.1)
#         if connection.shell_channel.recv_ready():  # some banner just after open ssh
#             connection.receive()
#         request = "exit\n"
#         bytes2send = request.encode("utf-8")
#         if isinstance(connection, ThreadedSshShell):
#             connection.moler_connection.subscribe(receiver, connection_closed_handler)
#         connection.send(bytes2send)
#         time.sleep(0.1)
#         if isinstance(connection, ThreadedSshShell):
#             receiver_called.wait(timeout=0.5)
#             echo_bytes = received_data
#         else:
#             echo_bytes = connection.receive(timeout=0.5)
#         echo = echo_bytes.decode("utf-8")
#         assert "exit" in echo
#         with pytest.raises(RemoteEndpointDisconnected):
#             connection.send(bytes2send)
#         assert connection.shell_channel is None
#         assert connection.ssh_transport is None

# --------------------------- resources ---------------------------


def import_class(packet_prefixed_class_name):
    module_name, class_name = packet_prefixed_class_name.rsplit('.', 1)
    module = importlib.import_module(module_name)
    connection_class = getattr(module, class_name)
    return connection_class

#########################################################################
# Connection like SshShell is passive connection - needs pulling for data
# uses receive() API
#########################################################################
@pytest.fixture(params=['io.raw.sshshell.SshShell'])
def passive_sshshell_connection_class(request):
    connection_class = import_class('moler.' + request.param)
    return connection_class


######################################################################################################################
# Connection like ThreadedSshShell is active connections - pushes data by itself (same model as asyncio, Twisted, etc)
# uses data_received() API which delivers data to embedded moler_connection
######################################################################################################################
@pytest.fixture(params=['io.raw.sshshell.ThreadedSshShell'])
def active_sshshell_connection_class(request):
    connection_class = import_class('moler.' + request.param)
    return connection_class


@pytest.fixture(params=['io.raw.sshshell.SshShell', 'io.raw.sshshell.ThreadedSshShell'])
def sshshell_connection(request):
    from moler.threaded_moler_connection import ThreadedMolerConnection
    connection_class = import_class('moler.' + request.param)
    ######################################################################################
    # SshShell and ThreadedSshShell differ in API - ThreadedSshShell gets moler_connection
    # Why - see comment in sshshell.py
    ######################################################################################
    if "Threaded" in request.param:
        moler_conn = ThreadedMolerConnection(decoder=lambda data: data.decode("utf-8"),
                                             encoder=lambda data: data.encode("utf-8"))
        connection = connection_class(moler_connection=moler_conn,
                                      host='localhost', port=22, username='molerssh', password='moler_password')
    else:
        connection = connection_class(host='localhost', port=22, username='molerssh', password='moler_password')
    return connection


@pytest.fixture
def active_sshshell_connection(active_sshshell_connection_class):
    from moler.threaded_moler_connection import ThreadedMolerConnection
    connection_class = active_sshshell_connection_class
    moler_conn = ThreadedMolerConnection(decoder=lambda data: data.decode("utf-8"),
                                         encoder=lambda data: data.encode("utf-8"))
    connection = connection_class(moler_connection=moler_conn,
                                  host='localhost', port=22, username='molerssh', password='moler_password')
    return connection


@pytest.fixture
def mocked_logger():
    class MyLogger(object):
        def __init__(self):
            self.calls = []

        def debug(self, msg):
            msg_without_details = msg.split(" |", 1)
            self.calls.append("DEBUG: " + msg_without_details[0])

        def info(self, msg):
            msg_without_details = msg.split(" |", 1)
            self.calls.append(" INFO: " + msg_without_details[0])

    logger = MyLogger()
    return logger
