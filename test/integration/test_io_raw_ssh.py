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


def test_can_open_and_close_connection_as_context_manager(ssh_connection_class):

    connection = ssh_connection_class(host='localhost', port=22, username='ute', password='ute')
    with connection.open():
        assert connection.shell_channel.get_transport().is_authenticated()
    assert connection.ssh_client.get_transport() is None

    with connection:
        assert connection.shell_channel.get_transport().is_authenticated()
    assert connection.ssh_client.get_transport() is None


# --------------------------- resources ---------------------------


@pytest.fixture(params=['io.raw.ssh.Ssh'])
def ssh_connection_class(request):
    module_name, class_name = request.param.rsplit('.', 1)
    module = importlib.import_module('moler.{}'.format(module_name))
    connection_class = getattr(module, class_name)
    return connection_class
