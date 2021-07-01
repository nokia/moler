# -*- coding: utf-8 -*-
"""
External-IO connections based on raw sockets.

The only 3 requirements for these connections are:
(1) store Moler's connection inside self.moler_connection attribute
(2) plugin into Moler's connection the way IO outputs data to external world:

    self.moler_connection.how2send = self.send

(3) forward IO received data into self.moler_connection.data_received(data)
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import logging
import select
import socket
import sys
import threading
import contextlib

from moler.io.io_exceptions import ConnectionTimeout
from moler.io.io_exceptions import RemoteEndpointDisconnected
from moler.io.io_exceptions import RemoteEndpointNotConnected
from moler.io.raw import TillDoneThread
import datetime
from moler.util import tracked_thread


# TODO: logging - want to know what happens on GIVEN connection
# TODO: logging - rethink details


class Tcp(object):
    r"""
    Implementation of TCP connection using python builtin modules.::

        socket.send    /|           |\
                      / +-----------+ \
                     /    host:port    \  TCP server
        socket.recv  \                 /
                      \ +-----------+ /
                       \|           |/

    """
    def __init__(self, port, host="localhost", receive_buffer_size=64 * 4096,
                 logger=None):
        """Initialization of TCP connection."""
        super(Tcp, self).__init__()
        # TODO: do we want connection.name?
        self.host = host
        self.port = port
        self.receive_buffer_size = receive_buffer_size
        self.logger = logger  # TODO: build default logger if given is None?
        self.socket = None

    def open(self):
        """
        Open TCP connection.

        Should allow for using as context manager: with connection.open():
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        blocking = 1
        if sys.platform.startswith('java'):  # Program runs under Jython
            blocking = 0  # Jython  limitation
        self.socket.setblocking(blocking)
        self._debug('connecting to {}'.format(self))
        self.socket.connect((self.host, self.port))
        self._debug('connection {} is open'.format(self))
        return contextlib.closing(self)

    def close(self):
        """
        Close TCP connection.

        Connection should allow for calling close on closed/not-open connection.
        """
        if self.socket is not None:
            self._debug('closing {}'.format(self))
            self.socket.close()
            self.socket = None
        self._debug('connection {} is closed'.format(self))

    def __enter__(self):
        """While working as context manager connection should auto-open if it's not open yet."""
        if self.socket is None:
            self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False  # reraise exceptions if any

    def send(self, data):
        """
        Send data via TCP service.

        :param data: data
        :type data: str
        """
        try:
            self.socket.send(data)
        except socket.error as serr:
            if (serr.errno == 10054) or (serr.errno == 10053):
                self._close_ignoring_exceptions()
                info = "{} during send msg '{}'".format(serr.errno, data)
                raise RemoteEndpointDisconnected('Socket error: ' + info)
            else:
                raise

    def receive(self, timeout=30):
        """
        Receive data.

        :param timeout: time-out, default 30 sec
        :type timeout: float
        """
        if not self.socket:
            raise RemoteEndpointNotConnected()
        ready = select.select([self.socket], [], [], timeout)
        if ready[0]:
            try:
                data = self.socket.recv(self.receive_buffer_size)
            except socket.error as serr:
                if (serr.errno == 10054) or (serr.errno == 10053):
                    self._close_ignoring_exceptions()
                    raise RemoteEndpointDisconnected(serr.errno)
                else:
                    raise serr

            if not data:
                self._close_ignoring_exceptions()
                raise RemoteEndpointDisconnected()
            return data

        else:
            # don't want to show class name - just tcp address
            # want same output from any implementation of TCP-connection
            info = "Timeout (> %.3f sec) on {}".format(timeout, self)
            raise ConnectionTimeout(info)

    def _close_ignoring_exceptions(self):
        try:
            self.socket.close()
        except Exception:
            pass
        self.socket = None

    def __str__(self):
        address = 'tcp://{}:{}'.format(self.host, self.port)
        return address

    def _debug(self, msg):  # TODO: refactor to class decorator or so
        if self.logger:
            self.logger.debug(msg)


class ThreadedTcp(Tcp):
    """
    TCP connection feeding Moler's connection inside dedicated thread.

    This is external-IO usable for Moler since it has it's own runner
    (thread) that can work in background and pull data from TCP connection.
    """

    def __init__(self, moler_connection,
                 port, host="localhost", receive_buffer_size=64 * 4096,
                 logger=None):
        """Initialization of TCP-threaded connection."""
        super(ThreadedTcp, self).__init__(port=port, host=host,
                                          receive_buffer_size=receive_buffer_size,
                                          logger=logger)
        self.pulling_thread = None
        # make Moler happy (3 requirements) :-)
        self.moler_connection = moler_connection  # (1)
        self.moler_connection.how2send = self.send  # (2)

    def open(self):
        """Open TCP connection & start thread pulling data from it."""
        ret = super(ThreadedTcp, self).open()
        done = threading.Event()
        self.pulling_thread = TillDoneThread(target=self.pull_data,
                                             done_event=done,
                                             kwargs={'pulling_done': done})
        self.pulling_thread.start()
        return ret

    def close(self):
        """Close TCP connection & stop pulling thread."""
        if self.pulling_thread:
            self.pulling_thread.join()
            self.pulling_thread = None
        super(ThreadedTcp, self).close()

    @tracked_thread.log_exit_exception
    def pull_data(self, pulling_done):
        """Pull data from TCP connection."""
        logging.getLogger("moler_threads").debug("ENTER {}".format(self))
        heartbeat = tracked_thread.report_alive()
        while not pulling_done.is_set():
            if next(heartbeat):
                logging.getLogger("moler_threads").debug("ALIVE {}".format(self))
            try:
                data = self.receive(timeout=0.1)
                if data:
                    # make Moler happy :-)
                    self.moler_connection.data_received(data, datetime.datetime.now())  # (3)
            except ConnectionTimeout:
                continue
            except RemoteEndpointNotConnected:
                break
            except RemoteEndpointDisconnected:
                break
        if self.socket is not None:
            self._close_ignoring_exceptions()
        logging.getLogger("moler_threads").debug("EXIT  {}".format(self))
