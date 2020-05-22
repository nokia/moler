# -*- coding: utf-8 -*-
"""
External-IO connections based on Paramiko.

The only 3 requirements for these connections are:
(1) store Moler's connection inside self.moler_connection attribute
(2) plugin into Moler's connection the way IO outputs data to external world:

    self.moler_connection.how2send = self.send

(3) forward IO received data into self.moler_connection.data_received(data)
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import socket
import sys
import threading
import contextlib
import paramiko
import time
import getpass
from moler.helpers import instance_id

from moler.io.io_exceptions import ConnectionTimeout
from moler.io.io_exceptions import RemoteEndpointDisconnected
from moler.io.io_exceptions import RemoteEndpointNotConnected
from moler.io.io_connection import IOConnection
from moler.io.raw import TillDoneThread
import datetime


# TODO: logging - want to know what happens on GIVEN connection
# TODO: logging - rethink details


class SshShell(object):
    """
    Implementation of 'remote shell over Ssh' connection using python Paramiko module

    This connection is not intended for one-shot actions like execute_command of paramiko.
    It's purpose is to provide continuous stream of bytes from remote shell.
    Moreover, it works with Pty assigned to remote shell to enable interactive dialog
    like asking for login or password.
    """
    _channels_of_transport = {}  # key is instance_id(transport), value is list of channel IDs

    def __init__(self, host, port=22, username=None, password=None, receive_buffer_size=64 * 4096,
                 logger=None, existing_client=None):
        """Initialization of SshShell connection."""
        super(SshShell, self).__init__()
        # TODO: do we want connection.name?
        self.host = host
        self.port = port
        self.username = getpass.getuser() if username is None else username
        self.password = password
        self.receive_buffer_size = receive_buffer_size
        self.logger = logger  # TODO: build default logger if given is None?

        self.ssh_client = existing_client if existing_client else paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._shell_channel = None  # MOST IMPORTANT
        self.timeout = None
        self.await_ready_tick_resolution = 0.01

    @classmethod
    def from_sshshell(cls, sshshell, logger=None):
        assert isinstance(sshshell, SshShell)
        assert issubclass(cls, SshShell)
        new_sshshell = cls(host=sshshell.host, port=sshshell.port,
                           username=sshshell.username, password=sshshell.password,
                           receive_buffer_size=sshshell.receive_buffer_size,
                           logger=logger, existing_client=sshshell.ssh_client)
        return new_sshshell

    @property
    def shell_channel(self):
        return self._shell_channel

    @property
    def ssh_transport(self):
        return self.ssh_client.get_transport()

    def settimeout(self, timeout):
        if (self.timeout is None) or (timeout != self.timeout):
            if self._shell_channel:
                self._shell_channel.settimeout(timeout)
                self.timeout = timeout

    def open(self):
        """
        Open SshShell connection.

        Should allow for using as context manager: with connection.open():
        """
        if self._shell_channel is None:
            self._debug('connecting to {}'.format(self))

            transport = self.ssh_client.get_transport()
            if transport is None:
                self.ssh_client.connect(self.host, username=self.username, password=self.password)
                transport = self.ssh_client.get_transport()
                action = "established"
            else:
                action = "reusing"
            transport_info = ['local version = {}'.format(transport.local_version),
                              'remote version = {}'.format(transport.remote_version),
                              'using socket = {}'.format(transport.sock)]
            self._debug('  {} ssh transport to {}:{} |{}\n    {}'.format(action, self.host, self.port, transport,
                                                                         "\n    ".join(transport_info)))
            self._shell_channel = self.ssh_client.invoke_shell()  # newly created channel will be connected to Pty
            self._remember_channel_of_transport(self._shell_channel)
            self._debug('  established shell ssh to {}:{} [channel {}] |{}'.format(self.host, self.port,
                                                                                   self._shell_channel.get_id(),
                                                                                   self._shell_channel))
        self._info('connection {} is open'.format(self))
        return contextlib.closing(self)

    @classmethod
    def _remember_channel_of_transport(cls, channel):
        transport_id = instance_id(channel.get_transport())
        channel_id = channel.get_id()
        if transport_id in cls._channels_of_transport:
            cls._channels_of_transport[transport_id].append(channel_id)
        else:
            cls._channels_of_transport[transport_id] = [channel_id]

    @classmethod
    def _forget_channel_of_transport(cls, channel):
        transport_id = instance_id(channel.get_transport())
        channel_id = channel.get_id()
        if transport_id in cls._channels_of_transport:
            cls._channels_of_transport[transport_id].remove(channel_id)
            if len(cls._channels_of_transport[transport_id]) == 0:
                del cls._channels_of_transport[transport_id]

    @classmethod
    def _num_channels_of_transport(cls, transport):
        transport_id = instance_id(transport)
        if transport_id in cls._channels_of_transport:
            return len(cls._channels_of_transport[transport_id])
        return 0

    def close(self):
        """
        Close SshShell connection. Close channel of that connection.

        Connection should allow for calling close on closed/not-open connection.
        """
        if self._shell_channel is not None:
            self._debug('closing {}'.format(self))
        self._close()

    def _close(self):
        which_channel = ""
        if self._shell_channel is not None:
            which_channel = "[channel {}] ".format(self._shell_channel.get_id())
            self._shell_channel.close()
            time.sleep(0.05)  # give Paramiko threads time to catch correct value of status variables
            self._debug('  closed shell ssh to {}:{} {}|{}'.format(self.host, self.port,
                                                                   which_channel,
                                                                   self._shell_channel))
            self._forget_channel_of_transport(self._shell_channel)
            self._shell_channel = None
        transport = self.ssh_client.get_transport()
        if transport is not None:
            if self._num_channels_of_transport(transport) == 0:
                self._debug('  closing ssh transport to {}:{} |{}'.format(self.host, self.port, transport))
                self.ssh_client.close()
        self._info('connection {} {}is closed'.format(self, which_channel))

    def __enter__(self):
        """While working as context manager connection should auto-open if it's not open yet."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False  # reraise exceptions if any

    def __str__(self):
        if self._shell_channel:
            shell_channel_id = self._shell_channel.get_id()
            address = 'ssh://{}@{}:{} [channel {}]'.format(self.username, self.host, self.port, shell_channel_id)
        else:
            address = 'ssh://{}@{}:{}'.format(self.username, self.host, self.port)
        return address

    def send(self, data, timeout=1):
        """
        Send data via SshShell connection.

        :param data: data
        :type data: bytes
        :param timeout: max time to spend on sending all data, default 1 sec
        :type timeout: float
        """
        if not self._shell_channel:
            raise RemoteEndpointNotConnected()
        assert timeout > 0.0
        try:
            self._send(data, timeout)
        except socket.error as serr:
            if "Socket is closed" in str(serr):
                self._close()
                info = "{} during send msg '{}'".format(serr, data)
                raise RemoteEndpointDisconnected('Socket error: ' + info)
            else:
                raise  # let any other error be visible

    def _send(self, data, timeout=1.0):
        start_time = time.time()
        nb_bytes_to_send = len(data)
        nb_bytes_sent = 0
        data2send = data
        while True:
            if self._shell_channel.send_ready():
                chunk_bytes_sent = self._shell_channel.send(data2send)
                nb_bytes_sent += chunk_bytes_sent
            else:
                time.sleep(self.await_ready_tick_resolution)
                nb_bytes_sent = 0
            if nb_bytes_sent >= nb_bytes_to_send:
                break
            if time.time() - start_time >= timeout:
                send_status = '[{} of {} bytes] {}'.format(nb_bytes_sent, nb_bytes_to_send, data)
                # don't want to show class name - just ssh address
                # want same output from any implementation of SshShell-connection
                info = "Timeout (> {:.3f} sec) on {}, sent {}".format(timeout, self, send_status)
                raise ConnectionTimeout(info)
            data2send = data[nb_bytes_sent:]

    def receive(self, timeout=30.0):
        """
        Receive data.

        :param timeout: max time to await for data, default 30 sec
        :type timeout: float
        """
        self.settimeout(timeout=timeout)
        data = self.recv()
        return data

    def recv(self):
        """Receive data."""
        if not self._shell_channel:
            raise RemoteEndpointNotConnected()
        try:
            # ensure we will never block in recv()
            if not self._shell_channel.gettimeout():
                self._shell_channel.settimeout(self.await_ready_tick_resolution)
            data = self._shell_channel.recv(self.receive_buffer_size)
        except socket.timeout:
            # don't want to show class name - just ssh address
            # want same output from any implementation of SshShell-connection
            info = "Timeout (> {:.3f} sec) on {}".format(self.timeout, self)
            raise ConnectionTimeout(info)

        if not data:
            self._debug("shell ssh channel closed for {}".format(self))
            self._close()
            raise RemoteEndpointDisconnected()

        return data

    def _debug(self, msg):
        if self.logger:
            self.logger.debug(msg)

    def _info(self, msg):
        if self.logger:
            self.logger.info(msg)


##################################################################################################################
# SshShell and ThreadedSshShell differ in API - ThreadedSshShell gets moler_connection
# It is intentional architecture decision: SshShell has much looser binding with moler.
# Thanks to this it's reuse possibility is wider.
# As a consequence ThreadedSshShell uses SshShell via composition.
#
# Moreover, SshShell is passive connection - needs pulling for data
#           and ThreadedSshShell is active connection - pushes data by itself (same model as asyncio, Twisted, etc)
###################################################################################################################


class ThreadedSshShell(IOConnection):
    """
    SshShell connection feeding Moler's connection inside dedicated thread.

    This is external-IO usable for Moler since it has it's own runner
    (thread) that can work in background and pull data from SshShell connection.
    """

    def __init__(self, moler_connection,
                 host, port=22, username=None, password=None,
                 receive_buffer_size=64 * 4096,
                 logger=None,
                 existing_client=None):
        """Initialization of SshShell-threaded connection."""
        super(ThreadedSshShell, self).__init__(moler_connection=moler_connection)
        self.sshshell = SshShell(host=host, port=port, username=username, password=password,
                                 receive_buffer_size=receive_buffer_size,
                                 logger=logger, existing_client=existing_client)
        self.pulling_thread = None
        self.pulling_timeout = 0.1
        self._pulling_done = threading.Event()

    @classmethod
    def from_sshshell(cls, moler_connection, sshshell, logger=None):
        if isinstance(sshshell, ThreadedSshShell):
            sshshell = sshshell.sshshell
        assert isinstance(sshshell, SshShell)
        assert issubclass(cls, ThreadedSshShell)
        new_sshshell = cls(moler_connection=moler_connection, host=sshshell.host, port=sshshell.port,
                           username=sshshell.username, password=sshshell.password,
                           receive_buffer_size=sshshell.receive_buffer_size,
                           logger=logger, existing_client=sshshell.ssh_client)
        return new_sshshell

    @property
    def ssh_transport(self):
        return self.sshshell.ssh_transport

    @property
    def shell_channel(self):
        return self.sshshell.shell_channel

    def __str__(self):
        address = self.sshshell.__str__()
        return address

    def open(self):
        """Open SshShell connection & start thread pulling data from it."""
        was_closed = self.shell_channel is None
        self.sshshell.open()
        is_open = self.shell_channel is not None
        if was_closed and is_open:
            self._notify_on_connect()
        if self.pulling_thread is None:
            # set reading timeout in same thread where we open shell and before starting pulling thread
            self.sshshell.settimeout(timeout=self.pulling_timeout)
            self._pulling_done.clear()
            self.pulling_thread = TillDoneThread(target=self.pull_data,
                                                 done_event=self._pulling_done,
                                                 kwargs={'pulling_done': self._pulling_done})
            self.pulling_thread.start()
        return contextlib.closing(self)

    def close(self):
        """Close SshShell connection & stop pulling thread."""
        self._pulling_done.set()
        if self.pulling_thread:
            self.pulling_thread.join()  # pull_data will do self.sshshell.close()
            self.pulling_thread = None

    def send(self, data, timeout=1):
        """
        Send data via SshShell connection.

        :param data: data
        :type data: bytes
        :param timeout: max time to spend on sending all data, default 1 sec
        :type timeout: float
        """
        self.sshshell.send(data=data, timeout=timeout)

    def receive(self):
        """
        Pull data bytes from external-IO:

            data = io_connection.receive()

        data is intended to forward into Moler's connection:

            self.moler_connection.data_received(data)

        """
        data = self.sshshell.recv()
        return data

    def pull_data(self, pulling_done):
        """Pull data from SshShell connection."""
        already_notified = False
        while not pulling_done.is_set():
            try:
                data = self.receive()
                if data:
                    self.data_received(data, datetime.datetime.now())  # (3)
            except ConnectionTimeout:
                continue
            except RemoteEndpointNotConnected:
                break
            except RemoteEndpointDisconnected:
                self._notify_on_disconnect()
                already_notified = True
                break
        was_open = self.shell_channel is not None
        self.sshshell.close()
        is_closed = self.shell_channel is None
        if was_open and is_closed and (not already_notified):
            self._notify_on_disconnect()
